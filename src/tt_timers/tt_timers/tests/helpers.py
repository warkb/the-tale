import os

from tt_web import utils
from tt_web.common import semaphore
from tt_web.tests import helpers as web_helpers

from .. import service
from .. import operations


class BaseTests(web_helpers.BaseTests):

    def create_application(self):
        return service.create_application(get_config(), loop=self.loop)

    async def clean_environment(self, app=None):
        semaphore.clear()
        await operations.clean_database()


def get_config():
    config_path = os.path.join(os.path.dirname(__file__), 'fixtures', 'config.json')
    return utils.load_config(config_path)
