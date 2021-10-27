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
from monitor.environment.context_manager import ContextManager
from monitor.ui.user_interface_controller import UserInterfaceController
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import logging
from monitor.api.proxy import ApiProxy
from monitor.sys.system import service_boot, main
from monitor.environment.thread_manager import ThreadManager
# from monitor.microscope.microscope import Microscope as scope
from monitor.environment.context_manager import ContextManager
from monitor.ui.main import UserInterfaceController

# Initiate Logging
_logger = logging.getLogger(__name__)

# setup thread watch
thread_monitor = ThreadManager().start()
# microscope init
# scope.init()
with ContextManager() as context:
    mode = context.get_env('MONITOR_MODE')

if mode == 'headless':
    _logger.debug("Entering Headless Mode")
    ApiProxy()
    main()
    thread_monitor.join()
elif mode == 'service':
    _logger.info("Entering Service Mode")
    # start ui
    uic = UserInterfaceController()
    service_boot()
    # load runtime models from cache into state manager
    uic.service_loop()
elif mode == 'monitor':
    _logger.info("Entering Monitor Mode")
    # start ui
    uic = UserInterfaceController()
    ApiProxy()
    main()
    uic.ui_loop()
