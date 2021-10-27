#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
System Logger
=============
Modified: 2020-11

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
import sys
import os
import re
import logging
import logging.config
import yaml
import yaml.nodes
import yaml.loader
from pathlib import Path
from boto3.session import Session


def path_constructor(loader: yaml.loader.SafeLoader, node: yaml.nodes.ScalarNode) -> str:
    """
    Extract the matched value, expand env variable, and replace the match

    :raises IndexError: if environment variable was not found and no default was specified
    :returns: string replacement
    """
    value = loader.construct_scalar(node)
    match = re.compile(r'.*\$\{([^}^{]+)\}.*').match(value)
    env = os.environ[match.group(1)]
    return value.replace('${' + '{}'.format(match.group(1)) + '}', env)


def config() -> None:
    yaml.add_implicit_resolver('!path', re.compile(
        r'.*\$\{([^}^{]+)\}.*'), None, yaml.loader.SafeLoader)
    yaml.add_constructor('!path', path_constructor, yaml.loader.SafeLoader)
    if os.environ.get('MONITOR_ENV') is None:
        print("CI environment detected. Skipping logging configuration step")
        return
    if os.environ['MONITOR_ENV'] == 'production':
        LOG_CONFIG_FILENAME = "prod_config.yml"
    else:
        # for development environment we will store logs in /var/log/iris
        LOG_PATH = os.environ['SNAP_DATA']
        if LOG_PATH is not None and not os.path.isdir(LOG_PATH):
            os.makedirs(LOG_PATH, mode=0o777, exist_ok=True)
        LOG_CONFIG_FILENAME = "dev_config.yml"
        # using split '.' to remove logs for rolling file handlers with format: <name>.log.<number>
        LOGS = list(
            filter(
                lambda file: len(file.split('.')) > 1 and file.split('.') == 'log',
                os.listdir(path=LOG_PATH)
            )
        )
        for log in LOGS:
            os.remove(log)

    # NOTE: config file should be in same relative directory as this script
    CONFIG_PATH = Path(__file__).parent.joinpath(LOG_CONFIG_FILENAME)

    # bind logging to config file
    # verify path existance before initializing logger file configuration
    try:
        # load config from .yaml
        with open(CONFIG_PATH) as conf:
            try:
                user_cfg = yaml.safe_load(conf)
            except yaml.YAMLError as exc:
                logging.exception("Error parsing yaml: %s", exc)
            except IndexError as exc:
                logging.exception("Environment variable required but was not specified: %s", exc)
                sys.exit(1)
            else:
                if os.environ['MONITOR_ENV'] == 'production':
                    # configure cloud watch logging solution for production
                    # for production environment we will publish logs to cloudwatch
                    # setup IAM credentials for cloud watch logging
                    boto3_session = Session(
                        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
                        aws_secret_access_key=os.environ.get('AWS_SECRET_KEY'),
                        region_name=os.environ.get('AWS_REGION')
                    )
                    for _, value in user_cfg['handlers'].items():
                        value['boto3_session'] = boto3_session
                logging.config.dictConfig(user_cfg)
                logging.info('Configuring logger using dict config')
    except FileNotFoundError:
        print("Logging config file not found in expected absolute path: {}".format(CONFIG_PATH))
    else:
        print("Logging configuration successful.")
