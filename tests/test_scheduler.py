#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unittest for Scheduler
======================
Date: 2021-06

Dependencies:
-------------
```
import unittest
from unittest.mock import Mock

from app.monitor.event_handler.event_handler import EventHandler
from app.monitor.scheduler.imaging import Imaging
from app.monitor.scheduler.setpoint import Setpoint
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import imp
import math
import time
import sched
import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from monitor.scheduler import scheduler


class TestSchedulers(unittest.TestCase):

    def setUp(self):
        def kill_patches():  # Create a cleanup callback that undoes our patches
            patch.stopall()  # Stops all patches started with start()
            imp.reload(scheduler)  # Reload our mqtt module which restores the original decorator
        # We want to make sure this is run so we do this in addCleanup instead of tearDown
        self.addCleanup(kill_patches)
        # Now patch the decorator where the decorator is being imported from
        # The lambda makes our decorator into a pass-thru. Also, don't forget to call start()
        patch('monitor.environment.thread_manager.ThreadManager.threaded',
              lambda *x, **y: lambda f: f).start()
        patch('monitor.environment.thread_manager.ThreadManager.set_name',
              lambda *x, **y: lambda f: f).start()
        patch('monitor.environment.thread_manager.ThreadManager.lock',
              lambda *x, **y: lambda f: f).start()
        imp.reload(scheduler)  # Reloads the mqtt.py module which applies our patched decorator
        with patch.object(scheduler.Scheduler, 'schedule_runner'):
            self.scheduler = scheduler.Scheduler()

    def tearDown(self):
        del self.scheduler

    def test_repr(self):
        """
        Test str representation
        """
        self.scheduler.__repr__()

    @patch.object(sched.scheduler, 'enterabs')
    def test_populate(self, enterabs: MagicMock):
        """
        Verify the queue is populated with the correct number of events
        """
        def callback(i: int, string: str = ""): ...
        priority = 0
        time = math.ceil(datetime.now().timestamp())
        self.scheduler.populate(time, priority, callback, 1, string="test")
        enterabs.assert_called_once_with(time, priority, callback, (1,), string="test")

    def test_purge_all(self):
        """
        Test scheduler purge
        """
        self.scheduler.sch = Mock()
        self.scheduler.sch.cancel = Mock()
        self.scheduler.sch.queue = [object()]
        self.scheduler.purge_queue()
        self.scheduler.sch.cancel.assert_called_once()

    @patch.object(time, 'sleep')
    @patch.object(sched.scheduler, 'run')
    def test_schedule_runner(self, run: MagicMock, sleep: MagicMock):
        """
        Test schedule runner loop

        :param run: [description]
        :type run: MagicMock
        :param sleep: [description]
        :type sleep: MagicMock
        """
        sleep.side_effect = InterruptedError
        self.scheduler.sch = Mock()
        self.scheduler.sch.empty.return_value = False
        # run.side_effect = RuntimeError
        with self.assertRaises(InterruptedError):
            self.scheduler.schedule_runner()
