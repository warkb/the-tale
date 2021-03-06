
import smart_imports

smart_imports.all()


class ActionsContainer(object):

    __slots__ = ('actions_list', 'is_single')

    def __init__(self):
        self.is_single = False
        self.actions_list = []

    def serialize(self):
        return {'actions': [action.serialize() for action in self.actions_list]}

    @classmethod
    def deserialize(cls, data):
        obj = cls()
        obj.actions_list = [prototypes.ACTION_TYPES[relations.ACTION_TYPE.index_value[action_data['type']]].deserialize(data=action_data)
                            for action_data in data.get('actions', [])]
        obj.is_single = obj._is_single

        return obj

    def initialize(self, hero):
        if not self.actions_list:
            prototypes.ActionIdlenessPrototype.create(hero=hero, _bundle_id=hero.account_id)
            self.is_single = True

        for action in self.actions_list:
            action.hero = hero

    def ui_info(self):
        return {'actions': [action.ui_info() for action in self.actions_list]}

    def find_path(self):
        for action in reversed(self.actions_list):
            if action.path is None:
                continue

            return action.path

        return None

    @property
    def _is_single(self):
        return all(action.SINGLE for action in self.actions_list)

    def push_action(self, action):
        self.actions_list.append(action)
        self.is_single = self._is_single

    def pop_action(self):
        action = self.actions_list.pop()
        self.is_single = self._is_single
        return action

    @property
    def current_action(self):
        return self.actions_list[-1]

    @property
    def has_actions(self):
        return len(self.actions_list)

    @property
    def number(self):
        return len(self.actions_list)

    def has_proxy_actions(self):
        return any(action.TYPE.is_META_PROXY for action in self.actions_list)

    def reset_to_idl(self):
        self.actions_list = self.actions_list[:1]

    def request_replane(self):
        for action in self.actions_list:
            action.replane_required = True
