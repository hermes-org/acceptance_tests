"""Starts the IPC Hermes 9852 test system in GUI mode, no build necessary."""

import os
import sys
import logging
import configparser

sys.path.append('app/')
sys.path.append('mgr/')

# pylint: disable=import-error, wrong-import-position
from hitmanager import HitmanagerApp
from hermes_test_manager import hermes_test_api

LOG_FILE = "hitmanager.log"
INI_FILE = "config.ini"
SECTION_SUT = "system.under.test"
SECTION_TM = "test.manager.listening.port"
SECTION_LOG = "logging"
# default values overriding those in test manager
SUT_HOST = '127.0.0.1'
SUT_PORT = '50101'
TEST_MANAGER_PORT = '50103'

def _create_default_config_file():
    """Create default config file to be helpful for new users."""
    parser = configparser.ConfigParser()
    parser.add_section(SECTION_SUT)
    parser.set(SECTION_SUT, 'host', SUT_HOST)
    parser.set(SECTION_SUT, 'port', SUT_PORT)
    parser.add_section(SECTION_TM)
    parser.set(SECTION_TM, 'port', TEST_MANAGER_PORT)
    parser.add_section(SECTION_LOG)
    parser.set(SECTION_LOG, 'level', 'INFO')
    with open(INI_FILE, 'w', encoding='utf-8') as configfile:
        parser.write(configfile)

if __name__ == '__main__':

    # read/create default config file if it does not exist
    if not os.path.isfile(INI_FILE):
        _create_default_config_file()

    hermes_conf = configparser.ConfigParser()
    hermes_conf.read(INI_FILE)
    ini_section = hermes_conf[SECTION_SUT]
    if ini_section is not None:
        hermes_test_api.system_under_test_address(ini_section.get('host', SUT_HOST),
                                                  ini_section.get('port', SUT_PORT))
    ini_section = hermes_conf[SECTION_TM]
    if ini_section is not None:
        hermes_test_api.testmanager_listening_port(ini_section.get('port', TEST_MANAGER_PORT))
    ini_section = hermes_conf[SECTION_LOG]
    log_lvl = logging.INFO
    if ini_section is not None:
        log_lvl = ini_section.get('level', 'INFO')

    hermes_test_api.setup_default_logging(LOG_FILE, log_lvl, ['hitmanager'])
    log = logging.getLogger('hitmanager')
    log.debug('Starting hitmanager')
    HitmanagerApp().run()
    log.debug('Exiting hitmanager')
