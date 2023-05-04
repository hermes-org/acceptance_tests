"""Starts the IPC Hermes 9852 test system in GUI mode, no build necessary."""

import logging

from app.hitmanager import HitmanagerApp # pylint: disable=import-error

LOG_FILE = "hitmanager.log"

if __name__ == '__main__':
    formatter = logging.Formatter('{"time": "%(asctime)s.%(msecs)d", "package": "%(name)s", "level": "%(levelname)s", %(message)s}',
                                  '%Y-%m-%dT%H:%M:%S')
    file_handler = logging.FileHandler(LOG_FILE, mode='w')
    file_handler.setFormatter(formatter)

    for log_name in ['hermes_test_api','ipc_hermes','hitmanager']:
        logger = logging.getLogger(log_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    logger.info('starting hitmanager')
    HitmanagerApp().run()
    logger.info('exiting hitmanager')
