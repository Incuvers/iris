#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Monitor __init__
=================
`Monitor` defines the python application that is run on the Incubator RPi.

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import time
import logging
from threading import Thread
from monitor.logs.config import system_logger
from monitor.__version__ import __version__

logger = logging.getLogger(__name__)
logger.info("Incuvers™ Monitor Version: %s", __version__)


def logger_config():
    while True:
        # configure system logger
        try:
            system_logger.config()
        except BaseException:
            time.sleep(60)
        else:
            break


try:
    system_logger.config()
except BaseException as exc:
    logger.exception(
        "%s\nFirst time logging configuration failed. Starting logging config backoff loop.", exc)
    Thread(target=logger_config, daemon=True).start()
