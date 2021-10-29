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

LOG_PATH = str(Path(__file__).parent.joinpath('logs/'))
LOG_CONFIG_FILENAME = "config.yml"
# NOTE: config file should be in same relative directory as this script
CONFIG_PATH = Path(__file__).parent.joinpath("logs/config/" + LOG_CONFIG_FILENAME)

# using split '.' to remove logs for rolling file handlers with format: <name>.log.<number>
LOGS = list(
    filter(
        lambda file: 'log' in file.split('.'),
        os.listdir(path=LOG_PATH)
    )
)
# purge old logs on new instance
for log in LOGS: os.remove(str(Path(__file__).parent.joinpath('logs/')) + '/' + log)
# bind logging to config file
# verify path existance before initializing logger file configuration
try:
    # load config from .yaml
    with open(CONFIG_PATH) as conf:
        try:
            user_cfg = yaml.safe_load(conf)
        except yaml.YAMLError as exc:
            logging.exception("Error parsing yaml: %s", exc)
        else:
            logging.config.dictConfig(user_cfg)
            logging.info('Configuring logger using dict config')
except FileNotFoundError:
    logging.exception(
        "Logging config file not found in expected absolute path: {}".format(CONFIG_PATH))
else:
    logging.info("Logging configuration successful.")
