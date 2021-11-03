# -*- coding: utf-8 -*-
"""
Monitor Init
============
Modified: 2021-10

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import os
import yaml
import logging
import logging.config
from pathlib import Path
from envyaml import EnvYAML

from monitor.logs.formatter import pformat
from monitor.__version__ import __version__

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)
logging.info("Incuvers™ Monitor Version: %s", __version__)


def logging_handler(config_path: Path, base_path: str) -> None:
    """
    Configure monitor logger using dict config and set the logging path

    :param config_path: path to log config
    :type config_path: Path
    :param base_path: logging path
    :type base_path: str
    """
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


def device_certs_handler() -> None: ...


logging_handler(
    config_path=Path(__file__).parent.joinpath("logs/config/config.yml"),
    base_path=os.environ.get("MONITOR_LOGS", str(Path(__file__).parent.joinpath('logs/')))
)

device_certs_handler()
