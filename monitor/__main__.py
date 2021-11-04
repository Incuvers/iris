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
import logging
from monitor.api.proxy import ApiProxy
from monitor.sys.system import service_boot, main
from monitor.environment.thread_manager import ThreadManager
from monitor.ui.main import UserInterfaceController

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
uic = UserInterfaceController(mode)

if mode == 'service':
    _logger.info("Entering Service Mode")
    service_boot()
    # load runtime models from cache into state manager
    uic.service_loop()
elif mode == 'monitor':
    _logger.info("Entering Monitor Mode")
    ApiProxy(base_url, base_path)
    main()
    uic.ui_loop()
