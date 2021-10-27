# -*- coding: utf-8 -*-
"""
Unittests for System Cache
==========================
Date: 2021-05

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
from monitor.environment.state_manager import StateManager
from monitor.models.icb import ICB
import time
import binascii
import unittest
from threading import Condition
from serial.serialutil import SerialException
from unittest.mock import MagicMock, Mock, call, patch

from monitor.tests import resources
from monitor.events.event import Event
from monitor.arduino_link import sensors


class TestSensors(unittest.TestCase):

    @patch("serial.Serial")
    @patch.object(Event, 'register')
    def setUp(self, mock_event: MagicMock, mock_serial: MagicMock):
        """
        Mock state manager subscription, event registration and serial interface 

        :param mock_sm: mocked state manager
        :type mock_sm: MagicMock
        :param mock_event: mocked Event object
        :type mock_event: MagicMock
        :param mock_serial: mocked serial interface
        :type mock_serial: MagicMock
        """
        def kill_patches():  # Create a cleanup callback that undoes our patches
            patch.stopall()  # Stops all patches started with start()
            imp.reload(sensors)  # Reload our mqtt module which restores the original decorator
        # We want to make sure this is run so we do this in addCleanup instead of tearDown
        self.addCleanup(kill_patches)
        # Now patch the decorator where the decorator is being imported from
        # The lambda makes our decorator into a pass-thru. Also, don't forget to call start()
        patch('monitor.environment.thread_manager.ThreadManager.threaded',
              lambda *x, **y: lambda f: f).start()
        patch('monitor.environment.thread_manager.ThreadManager.lock',
              lambda *x, **y: lambda f: f).start()
        imp.reload(sensors)  # Reloads the mqtt.py module which applies our patched decorator
        self.sensors = sensors.Sensors("")
        self.mock_event = mock_event
        self.mock_serial = mock_serial

    def tearDown(self):
        """
        Teardown sensors object
        """
        del self.sensors

    @patch.object(time, 'sleep', side_effect=InterruptedError)
    @patch('monitor.arduino_link.sensors.Sensors._process_requests', return_value=resources.ICB_CMD_STR)
    @patch('monitor.arduino_link.sensors.Sensors._validate_checksum', return_value=True)
    @patch('monitor.arduino_link.sensors.Sensors._parser', return_value=resources.ICB_SENSORFRAME)
    @patch('monitor.arduino_link.sensors.Sensors._update_accepted_sensorframe')
    @patch('monitor.arduino_link.sensors.Sensors._update_state')
    def test_monitor(self, _update_state: MagicMock, _update_accepted_sensorframe: MagicMock, _parser: MagicMock,
                     _validate_checksum: MagicMock, _process_requests: MagicMock, _: MagicMock):
        """
        Test monitor event event loop and exception handles
        """
        # test sanity
        self.sensors.buffer = {'CP': 20.0}
        self.mock_serial.return_value.readline.return_value = resources.ICB_READLINE
        with self.assertRaises(InterruptedError):
            self.sensors.monitor()
        _process_requests.assert_called_once_with(self.sensors.buffer)
        _update_state.assert_called_once_with(resources.ICB_SENSORFRAME)
        _update_accepted_sensorframe.assert_called_once_with(resources.ICB_SENSORFRAME)
        _process_requests.reset_mock()
        _update_state.reset_mock()
        _update_accepted_sensorframe.reset_mock()
        # test serial timeout
        self.sensors.buffer = {}
        self.mock_serial.return_value.readline.side_effect = SerialException
        with self.assertRaises(InterruptedError):
            self.sensors.monitor()
        _update_state.assert_not_called()
        self.mock_serial.return_value.readline.side_effect = None
        # test no buffer
        self.sensors.buffer = {}
        with self.assertRaises(InterruptedError):
            self.sensors.monitor()
        _process_requests.assert_not_called()
        _update_state.reset_mock()
        _update_accepted_sensorframe.reset_mock()
        # test parsing failure
        _parser.side_effect = ValueError
        with self.assertRaises(InterruptedError):
            self.sensors.monitor()
        _update_state.assert_not_called()
        # test sensorframe checksum failure
        _validate_checksum.return_value = False
        with self.assertRaises(InterruptedError):
            self.sensors.monitor()
        _update_state.assert_not_called()

    @patch.object(binascii, 'crc32')
    def test_validate_checksum(self, crc32: MagicMock):
        """
        Test icb readline message and checksum and exceptions

        :param crc32: mock crc32 function
        :type crc32: MagicMock
        """
        # test empty msg
        self.assertFalse(self.sensors._validate_checksum(""))
        # test bad splitting for both '~' and '$' cases
        self.assertFalse(self.sensors._validate_checksum("173~"))
        self.assertFalse(self.sensors._validate_checksum("173~4324$"))
        # test sanity
        crc32.return_value = 0x784f3423
        self.assertTrue(self.sensors._validate_checksum("173~784f3423$&TP|4600"))
        # # test failed crc
        crc32.return_value = 0x78f34231
        self.assertFalse(self.sensors._validate_checksum("173~784f3423$&TP|4600"))

    def test_parser(self):
        """
        Test string parser and malformed kvp handling
        """
        # test sanity
        self.assertDictEqual(self.sensors._parser(
            resources.ICB_READLINE.decode()), resources.ICB_SENSORFRAME)
        # test malformed kvp
        val = resources.ICB_SENSORFRAME.pop('TM')
        self.assertDictEqual(self.sensors._parser(
            resources.ICB_READLINE_MALFORMED.decode()), resources.ICB_SENSORFRAME)
        resources.ICB_SENSORFRAME['TM'] = val

    def test_update_state(self):
        """
        Test update state context.
        """
        self.sensors._update_state(resources.ICB_SENSORFRAME)

    @patch.object(Condition, 'notify_all', autospec=True)
    def test_updated_accepted_sensorframe(self, notify_all: MagicMock):
        """
        Test sensorframe, buffer comparison and conditional triggers

        :param notify_all: mock variable for threading condition
        :type notify_all: MagicMock
        """
        # test CT accepted
        self.sensors.buffer = {'CT': 37531}
        self.sensors._update_accepted_sensorframe(resources.ICB_SENSORFRAME)
        self.assertEqual(notify_all.call_count, 2)
        notify_all.reset_mock()
        # test CP, OP, TP accepted
        test_requests = [
            ('CP', resources.ICB_SENSORFRAME['CP']),
            ('OP', resources.ICB_SENSORFRAME['OP']),
            ('TP', resources.ICB_SENSORFRAME['TP'])
        ]
        for kvp in test_requests:
            with self.subTest("Testing {} acceptance".format(kvp)):
                self.sensors.buffer = {kvp[0]: kvp[1]}
                self.sensors._update_accepted_sensorframe(resources.ICB_SENSORFRAME)
                notify_all.assert_called_once()
                notify_all.reset_mock()
        # test unprocessed
        self.sensors.buffer = {'CT': 43213}
        self.sensors._update_accepted_sensorframe(resources.ICB_SENSORFRAME)
        notify_all.assert_called_once()

    @patch('monitor.arduino_link.sensors.Sensors.queue_buffer')
    @patch.object(Condition, 'wait', autospec=True)
    def test_send_co2_calibration_time(self, wait: MagicMock, queue_buffer: MagicMock):
        """
        Test co2 calibration time and exceptions

        :param wait: [description]
        :type wait: MagicMock
        :param mock_sm: [description]
        :type mock_sm: MagicMock
        """
        self.sensors.send_co2_calibration_time()
        wait.assert_called_once()
        queue_buffer.assert_called_once()
        wait.reset_mock()
        # call a second time and timeout?
        wait.return_value = False
        with self.assertRaises(TimeoutError):
            self.sensors.send_co2_calibration_time()

    @patch.object(Event, 'trigger')
    @patch.object(StateManager, '__enter__')
    @patch.object(Condition, 'wait', return_value=True, autospec=True)
    @patch('monitor.arduino_link.sensors.Sensors.queue_buffer', autospec=True)
    def test_validator(self, queue_buffer: MagicMock, wait: MagicMock, state: MagicMock, trigger: MagicMock):
        """
        Test validator callback and threading condition

        :param mock_sm: mocked state manager
        :type mock_sm: MagicMock
        :param queue_buffer: mocked queue_buffer
        :type queue_buffer: MagicMock
        :param wait: mocked threading.Condition.wait
        :type wait: MagicMock
        """
        state.return_value.icb = Mock(spec=ICB)
        # test candidate deltas against active state
        self.sensors.validator(Mock(spec=ICB))
        trigger.assert_has_calls(
            [
                call(True),
                call(True),
                call(True)
            ]
        )
        self.assertEqual(queue_buffer.call_count, 8)
        wait.assert_called_once()

    def test_queue_buffer(self):
        """
        Test queue buffer appending
        """
        # test valid key requests
        for key in ['TP', 'CP', 'OP', 'CT', 'HP', 'FP']:
            with self.subTest("Testing buffer request {}".format(key)):
                self.sensors.buffer = {}
                self.sensors.queue_buffer(key, 0.2)
                self.assertDictEqual(self.sensors.buffer, {key: 0.2})

    @patch.object(binascii, 'crc32')
    def test_process_request(self, mock_crc):
        """
        Test process request translation

        :param mock_crc: [description]
        :type mock_crc: [type]
        """
        mock_crc.return_value = 0xFFFFFFFF
        buf = {'TP': 37.5}
        ret = sensors.Sensors._process_requests(buf)
        self.assertEqual('7~ffffffff$TP|37.5\r\n', ret)
        buf = {'TP': 37.5, 'CP': 5.0}
        ret = sensors.Sensors._process_requests(buf)
        self.assertEqual('14~ffffffff$TP|37.5&CP|5.0\r\n', ret)
