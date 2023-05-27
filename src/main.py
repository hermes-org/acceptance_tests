"""Starts the IPC Hermes 9852 test system in GUI mode, no build necessary."""

import logging

 # pylint: disable=import-error
from app.hitmanager import HitmanagerApp
from mgr.hermes_test_manager.hermes_test_api import setup_default_logging

LOG_FILE = "hitmanager.log"

if __name__ == '__main__':
    setup_default_logging(LOG_FILE, logging.DEBUG, ['hitmanager'])
    log = logging.getLogger('hitmanager')
    log.info('Starting hitmanager')
    HitmanagerApp().run()
    log.info('Exiting hitmanager')
