# coding: utf-8
import time
import datetime
import math
import itertools

from collections import namedtuple

import Queue

from django.utils.log import getLogger

from dext.utils.decorators import nested_commit_on_success

from common.amqp_queues import BaseWorker
from common import postponed_tasks

from game.heroes.prototypes import HeroPrototype

from game.prototypes import SupervisorTaskPrototype

from game.pvp.models import BATTLE_1X1_STATE
from game.pvp.conf import pvp_settings
from game.pvp.prototypes import Battle1x1Prototype

class PvPBalancerException(Exception): pass


class QueueRecord(namedtuple('QueueRecord', ('account_id', 'created_at', 'battle_id', 'hero_level'))):
    __slots__ = ()

class BalancingRecord(namedtuple('BalancingRecord', ('min_level', 'max_level', 'record'))):
    __slots__ = ()


    def in_interval(self, level):
        return self.min_level <= level <= self.max_level

    def has_intersections(self, other):
        return self.in_interval(other.record.hero_level) and other.in_interval(self.record.hero_level)



class Worker(BaseWorker):

    def __init__(self, game_queue):
        super(Worker, self).__init__(logger=getLogger('the-tale.workers.game_pvp_balancer'), command_queue=game_queue)

    def set_supervisor_worker(self, supervisor_worker):
        self.supervisor_worker = supervisor_worker

    def run(self):

        while not self.exception_raised and not self.stop_required:
            try:
                cmd = self.command_queue.get_nowait()
                cmd.ack()
                self.process_cmd(cmd.payload)
            except Queue.Empty:
                if self.initialized:
                    self.do_balancing()
                time.sleep(pvp_settings.BALANCER_SLEEP_TIME)

    def cmd_initialize(self, worker_id):
        self.send_cmd('initialize', {'worker_id': worker_id})

    def process_initialize(self, worker_id):

        if self.initialized:
            self.logger.warn('WARNING: pvp balancer already initialized, do reinitialization')

        postponed_tasks.autodiscover()

        self.initialized = True
        self.worker_id = worker_id

        Battle1x1Prototype.reset_waiting_battles()

        self.arena_queue = {}

        self.logger.info('PVP BALANCER INITIALIZED')

        self.supervisor_worker.cmd_answer('initialize', self.worker_id)

    def cmd_stop(self):
        return self.send_cmd('stop')

    def process_stop(self):
        self.initialized = False
        self.supervisor_worker.cmd_answer('stop', self.worker_id)
        self.stop_required = True
        self.logger.info('PVP BALANCER STOPPED')

    def cmd_logic_task(self, account_id, task_id):
        return self.send_cmd('logic_task', {'task_id': task_id,
                                            'account_id': account_id})

    def process_logic_task(self, account_id, task_id):
        task = postponed_tasks.PostponedTaskPrototype.get_by_id(task_id)
        task.process(self.logger, pvp_balancer=self)
        task.do_postsave_actions()

    def add_to_arena_queue(self, hero_id):

        from accounts.prototypes import AccountPrototype

        hero = HeroPrototype.get_by_account_id(hero_id)

        if hero.account_id in self.arena_queue:
            return None

        battle = Battle1x1Prototype.create(AccountPrototype.get_by_id(hero.account_id))

        record = QueueRecord(account_id=battle.account_id,
                             created_at=battle.created_at,
                             battle_id=battle.id,
                             hero_level=hero.level)

        if record.account_id in self.arena_queue:
            raise PvPBalancerException('account %d already added in balancer queue' % record.account_id)

        self.arena_queue[record.account_id] = record

        return battle

    def leave_arena_queue(self, hero_id):

        hero = HeroPrototype.get_by_account_id(hero_id)

        battle = Battle1x1Prototype.get_active_by_account_id(hero.account_id)

        if not battle.state.is_waiting:
            return

        if battle.account_id not in self.arena_queue:
            self.logger.error('can not leave queue: battle %d in waiting state but no in arena queue' % battle.id)
            return

        del self.arena_queue[battle.account_id]

        battle.state = BATTLE_1X1_STATE.LEAVE_QUEUE
        battle.save()


    def _get_prepaired_queue(self):

        records = []
        records_to_remove = []

        time_in_level = float(pvp_settings.BALANCING_TIMEOUT) / pvp_settings.BALANCING_MAX_LEVEL_DELTA

        for record in self.arena_queue.values():

            time_delta = (datetime.datetime.now() - record.created_at).seconds

            if time_delta > pvp_settings.BALANCING_TIMEOUT:
                records_to_remove.append(record)
                continue

            balancing_record = BalancingRecord(min_level=math.floor(record.hero_level - pvp_settings.BALANCING_MIN_LEVEL_DELTA - time_delta / time_in_level),
                                               max_level=math.ceil(record.hero_level + pvp_settings.BALANCING_MIN_LEVEL_DELTA + time_delta / time_in_level),
                                               record=record)

            records.append(balancing_record)

        return sorted(records, key=lambda r: r.record.created_at), records_to_remove

    def _search_battles(self, records):

        battle_pairs = []
        records_to_exclude = []

        while records:

            current_record = records[0]

            records.pop(0)

            for index, record in enumerate(records):

                if current_record.has_intersections(record):
                    battle_pairs.append((current_record.record, record.record))
                    records.pop(index)
                    records_to_exclude.append(current_record.record)
                    records_to_exclude.append(record.record)
                    break

        return battle_pairs, records_to_exclude

    def _clean_queue(self, records_to_remove, records_to_exclude):
        for record in itertools.chain(records_to_remove, records_to_exclude):
            del self.arena_queue[record.account_id]

        if records_to_remove:
            Battle1x1Prototype.set_enemy_not_found_state_by_ids([record.battle_id for record in records_to_remove])
            self.logger.info('remove from queue request from accounts %r' % (records_to_remove, ))


    def _initiate_battle(self, record_1, record_2):
        from accounts.prototypes import AccountPrototype

        account_1 = AccountPrototype.get_by_id(record_1.account_id)
        account_2 = AccountPrototype.get_by_id(record_2.account_id)

        self.logger.info('start battle between accounts %d and %d' % (account_1.id, account_2.id))

        with nested_commit_on_success():
            Battle1x1Prototype.get_by_id(record_1.battle_id).set_enemy(account_2)
            Battle1x1Prototype.get_by_id(record_2.battle_id).set_enemy(account_1)

            task = SupervisorTaskPrototype.create_arena_pvp_1x1(account_1, account_2)

        self.supervisor_worker.cmd_add_task(task.id)

    def do_balancing(self):

        records, records_to_remove = self._get_prepaired_queue()

        battle_pairs, records_to_exclude = self._search_battles(records)

        for battle_pair in battle_pairs:
            self._initiate_battle(*battle_pair)

        self._clean_queue(records_to_remove, records_to_exclude)