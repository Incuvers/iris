#!/snap/iris/current/lib/python3.8/site-packages/python
# -*- coding: utf-8 -*-
"""
Daemon __init__
================
Updated: 2020-08

Initialize loggers

Dependancies
------------
from daemon.logs.config import daemon_logger

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from daemon.logs.config import daemon_logger

# This will configure the daemon processes to log to stdout
daemon_logger.config()
