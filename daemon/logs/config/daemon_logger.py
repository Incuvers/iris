#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Logger Config
=============
Modified: 2020-08

System logger configuration script.

Dependencies:
-------------
```
import logging.config
from pathlib import Path
import yaml
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
# blacklisted import
import yaml
import logging.config
from pathlib import Path


# NOTE: config file should be in same relative directory as this script
LOG_CONFIG_FILENAME = "log_config.yml"
CONFIG_PATH = Path(__file__).parent.joinpath(LOG_CONFIG_FILENAME)

def config():
    # bind logging to config file
    # verify path existance before initializing logger file configuration
    try:
        # load config from .yaml
        with open(CONFIG_PATH) as conf:
            config = yaml.load(conf, Loader=yaml.FullLoader)
            logging.config.dictConfig(config)

    except FileNotFoundError:
        print("Logging config file not found in expected absolute path: {}".format(CONFIG_PATH))
    except Exception as exc:
        print("Logging configuration failed: {}".format(exc))
    else:
        print("Logging configuration successful.")
