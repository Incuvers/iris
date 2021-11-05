# -*- coding: utf-8 -*-
"""
Unittests for Event
===================
Date: 2021-05

Dependencies:
-------------
```
import unittest
from unittest.mock import Mock
from monitor.events.event import Event
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import unittest
from unittest.mock import Mock
from monitor.events.event import Event


class TestEvents(unittest.TestCase):

    def setUp(self):
        logging.disable()
        self.event = Event("TEST_EVENT")

    def tearDown(self):
        del self.event
        logging.disable(logging.NOTSET)

    def test_str(self):
        """
        Test string repr
        """
        assert str(self.event) == "TEST_EVENT: []"

    def test_register(self):
        """
        Test event registration and priority sorting
        """
        # test single callback registration
        def fn(_): return None
        self.event.register(fn)
        self.assertEqual(self.event.registry[0][0], fn)
        self.assertEqual(self.event.registry[0][1], 1)
        self.assertEqual(self.event.registry[0][2], None)
        # test priority sorting
        def prio(_): return None
        def cond(_): return False
        self.event.register(prio, 0, cond)
        self.assertEqual(self.event.registry[0][0], prio)
        self.assertEqual(self.event.registry[1][0], fn)
        self.assertEqual(self.event.registry[0][2], cond)

    def test_trigger(self):
        """
        Test event callback execution engine and exception handling
        """
        callback = Mock(return_value=None)
        cond_callback = Mock(return_value=None)
        test_args = (1, "test")
        # test empty registry
        self.event.trigger(*test_args)
        # test sanity
        self.event.register(callback)
        self.event.trigger(*test_args)
        callback.assert_called_once_with(*test_args)
        # test false conditional execution
        self.event.register(cond_callback, condition=lambda *args, **kwargs: False)
        self.event.trigger(*test_args)
        cond_callback.assert_not_called()
        # test base exception
        callback.reset_mock()
        callback.side_effect = Exception
        self.event.trigger(*test_args)
