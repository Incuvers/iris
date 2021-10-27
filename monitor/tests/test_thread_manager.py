# -*- coding: utf-8 -*-
"""
Unittests for Thread Manager
============================
Date: 2021-06

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import logging
import time
import psutil
import unittest
import threading
from threading import Thread
from unittest.mock import MagicMock, Mock, patch

from monitor.events.event import Event
from monitor.environment.thread_manager import ThreadManager
from monitor.ui.static.settings import UISettings as uis


class TestThreadManager(unittest.TestCase):

    def setUp(self) -> None:
        logging.disable()
        self.tm = ThreadManager()

    def tearDown(self) -> None:
        del self.tm
        logging.disable(logging.NOTSET)

    @patch.object(time, 'sleep', side_effect=InterruptedError)
    @patch.object(psutil.Process, 'memory_percent')
    @patch.object(Event, 'trigger')
    def test_monitor(self, trigger: MagicMock, memory_percent: MagicMock, _: MagicMock):
        """
        Test memory alert monitoring

        :param trigger: mocked event trigger
        :type trigger: MagicMock
        :param memory_percent: mocked memory percent computation
        :type memory_percent: MagicMock
        :param _: boot out of loop
        :type _: MagicMock
        """
        # test alert
        memory_percent.return_value = self.tm.MEM_THRESH + 1
        with self.assertRaises(InterruptedError):
            self.tm._monitor()
        trigger.assert_called_once_with(uis.STATUS_ALERT)

    @patch.object(psutil.Process, 'nice')
    @patch.object(Thread, 'start')
    def test_start(self, start: MagicMock, nice: MagicMock):
        """
        Test thread start
        """
        # headless = False
        self.tm.start()
        nice.assert_called_once_with(-1)
        start.assert_called_once()

    def test_lock(self):
        """
        Test function lock decorator and return args
        """
        @self.tm.lock(self.tm.api_lock)
        def func() -> bool:
            self.assertTrue(self.tm.api_lock.locked())
            return True
        self.assertFalse(self.tm.api_lock.locked())
        self.assertTrue(func())

    @patch.object(ThreadManager, 'assign_name', **{'return_value': "test"})
    @patch('monitor.environment.thread_manager.current_thread')
    def test_set_name(self, current_thread: MagicMock, _: MagicMock):
        """
        Test thread name setting

        :param current_thread: [description]
        :type current_thread: MagicMock
        :param assign_name: [description]
        :type assign_name: MagicMock
        """
        @self.tm.set_name("test")
        def func() -> None: ...
        t = threading.Thread(target=func, daemon=True)
        t.start()
        t.join()
        self.assertEqual(current_thread.return_value.name, "test")

    @patch('monitor.environment.thread_manager.Thread', autospec=True)
    @patch.object(ThreadManager, 'assign_name', **{'return_value': "test"})
    def test_threaded(self, _: MagicMock, Thread: MagicMock):
        """
        Test 'threaded' decorator

        :param _: mocked thread manager check name
        :type _: MagicMock
        :param Thread: mocked threading init
        :type Thread: MagicMock
        """
        @self.tm.threaded(daemon=True)
        def function(test_arg: int, test_kwarg: str = "Test") -> None: ...
        function(1, test_kwarg="Ok")
        Thread.assert_called_once()

    @patch('monitor.environment.thread_manager.enumerate', return_value=[Mock(spec=Thread)])
    def test_assign_name(self, enumerate: MagicMock):
        """
        Test name assignment

        :param enumerate: mocked active thread objects
        :type enumerate: MagicMock
        """
        enumerate.return_value[-1].name = "test"
        # test sanity
        self.tm.assign_name("test")
        enumerate.return_value[-1].name = "test_1"
        self.tm.assign_name("test_1")
