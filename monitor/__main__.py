# -*- coding: utf-8 -*-
"""
Monitor __main__
=================
Modified: 2021-05

`Monitor` defines the python application that is run on IRIS.

Dependancies
------------
```
from monitor.microscope.microscope import Microscope
from monitor.events.event_handler import EventHandler
from monitor.sys.system import service_boot, system_boot
from monitor.environment.thread_manager import ThreadManager
from monitor.ui.user_interface_controller import UserInterfaceController
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import sys
import logging
import logging.config
from pathlib import Path
from envyaml import EnvYAML
from configparser import ConfigParser
from monitor.api.proxy import ApiProxy
from monitor.logs.formatter import pformat
from monitor.sys.system import service_boot, main
from monitor.environment.thread_manager import ThreadManager
from monitor.ui.main import UserInterfaceController


def logging_handler(config_path: Path, base_path: str) -> None:
    """
    Configure monitor logger using dict config and set the logging path

    :param config_path: path to log config
    :type config_path: Path
    :param base_path: logging path
    :type base_path: str
    """
    os.makedirs(base_path, mode=0o777, exist_ok=True)
    # using split '.' to remove logs for rolling file handlers with format: <name>.log.<number>
    logs = list(
        filter(
            lambda file: 'log' in file.split('.'),
            os.listdir(path=base_path)
        )
    )
    # purge old logs on new instance
    for log in logs: os.remove(base_path + '/' + log)
    # bind logging to config file
    # verify path existance before initializing logger file configuration
    try:
        # load config from .yaml
        env = EnvYAML(config_path).export()
        logging.info("Parsed logger config:%s", pformat(env))
        logging.config.dictConfig(env)
        logging.info('Configuring logger using dict config')
    except ValueError as exc:
        logging.exception(
            "Logging configuration failed due to missing environment variables: %s", exc)
    except FileNotFoundError:
        logging.exception(
            "Logging config file not found in expected absolute path: {}".format(config_path))
    else:
        logging.info("Logging configuration successful.")

def device_certs_handler(base_path: str) -> None:
    """
    Read device certs and export as environment variables for global access. 
    If device certs are missing exit with error code 2

    :param base_path: device certs base path
    :type base_path: str
    """
    if not os.path.exists(base_path + '/amqp.ini') or \
            not os.path.exists(base_path + '/device.ini'):
        logging.critical("Failed to identify device certs.")
        sys.exit(2)
    # instantiate
    config = ConfigParser()
    config.read(base_path + '/amqp.ini')
    os.environ['AMQP_USER'] = config.get('amqp', 'user')
    os.environ['AMQP_PASS'] = config.get('amqp', 'password')
    # parse existing file
    config.read(base_path + '/device.ini')
    os.environ['ID'] = config.get('iris', 'id')
    logging.info("Successfully exported device certs")

logging_handler(
    config_path=Path(__file__).parent.joinpath("logs/config/config.yml"),
    base_path=os.environ.get("MONITOR_LOGS", str(Path(__file__).parent.joinpath('logs/')))
)

device_certs_handler(
    base_path=os.environ.get("MONITOR_CERTS", str(
        Path(__file__).parent.parent.joinpath('instance/certs')))
)

# Initiate Logging
_logger = logging.getLogger(__name__)

# setup thread watch
ThreadManager().start()

# get environment variables
mode = os.environ.get('MONITOR_MODE', default="monitor")
_logger.info("Monitor mode: %s", mode)
base_url = os.environ.get('API_BASE_URL', default="https://api.prod.incuvers.com")
base_path = os.environ.get('API_BASE_PATH', default="/v1")

# start ui
uic = UserInterfaceController()

# if mode == 'service':
#     _logger.info("Entering Service Mode")
#     service_boot()
#     # load runtime models from cache into state manager
#     uic.service_loop()
# elif mode == 'monitor':
_logger.info("Entering Monitor Mode")
ApiProxy(base_url, base_path)
main()
uic.ui_loop()
