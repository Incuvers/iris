# -*- coding: utf-8 -*-
"""
Unittests for ICB Logger
========================
Date: 2021-09

Dependencies:
-------------
```
import unittest
from unittest.mock import Mock, patch
from monitor.arduino_link.sensors import Sensor
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import imp
import time
import logging
import unittest
import serial
from unittest.mock import MagicMock, patch

from monitor.arduino_link import icb_logger


class TestICBLogger(unittest.TestCase):

    @patch("serial.Serial")
    def setUp(self, mock_serial: MagicMock):
        """
        Mock serial interface

        :param mock_serial: mocked serial interface
        :type mock_serial: MagicMock
        """
        def kill_patches():  # Create a cleanup callback that undoes our patches
            patch.stopall()  # Stops all patches started with start()
            imp.reload(icb_logger)  # Reload our mqtt module which restores the original decorator
        # We want to make sure this is run so we do this in addCleanup instead of tearDown
        self.addCleanup(kill_patches)
        patch('monitor.environment.thread_manager.ThreadManager.threaded',
              lambda *x, **y: lambda f: f).start()
        imp.reload(icb_logger)  # Reloads the mqtt.py module which applies our patched decorator
        logging.disable()
        self.icb_logger = icb_logger.ICBLogger("/dev/ttyUSB0")
        self.mock_serial = mock_serial

    def tearDown(self):
        """
        Teardown sensors object
        """
        del self.icb_logger
        logging.disable(logging.NOTSET)

    def test_init(self):
        """
        Test serial initialization side effects
        """
        for exc in [serial.SerialException, FileNotFoundError]:
            with self.subTest("_post_request exception: {}".format(exc)):
                self.mock_serial.side_effect = exc
                il = icb_logger.ICBLogger("")
                self.assertEqual(il.serial_connection, None)

    @patch.object(time, 'sleep', side_effect=InterruptedError)
    def test_start(self, time):
        """
        Test start logging monitor
        """
        self.icb_logger._logger = MagicMock()
        self.mock_serial.return_value.readline.return_value = b'mock ICB log'
        with self.assertRaises(InterruptedError):
            self.icb_logger.start()
        self.icb_logger._logger.info.assert_called()
        self.mock_serial.reset_mock()
        self.icb_logger._logger.reset_mock()
        self.mock_serial.return_value.readline.side_effect = serial.SerialException
        with self.assertRaises(InterruptedError):
            self.icb_logger.start()
        self.icb_logger._logger.exception.assert_called()
