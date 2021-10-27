# -*- coding: utf-8 -*-
"""
Fluorescence Unittests
======================
Modified: 2021-07

Dependencies:
-------------
```
import logging
import wiringpi
from monitor.microscope.fluorescence.hardware import FluorescenceHardware
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import time
import unittest
from unittest.mock import MagicMock, call, patch, Mock
from monitor.sys import kernel
from monitor.events.event import Event
from monitor.events.pipeline import Pipeline
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager
from monitor.ui.static.settings import UISettings as uis
from monitor.exceptions.microscope import ChannelError, GSTDeviceError, LightingError, UvcdynctrlError


class TestMicroscope(unittest.TestCase):
    def setUp(self):
        self.mock_capture = Mock()
        mocked_modules = {
            'numpy': Mock(),
            'monitor.imaging.capture': self.mock_capture,
            'monitor.microscope.camera.capture_pipeline': Mock(),
            'monitor.microscope.camera.stream_pipeline': Mock(),
            'monitor.microscope.automatrix.automatrix': Mock(),
            'monitor.microscope.fluorescence.fluorescence': Mock(),
            'monitor.microscope.camera.properties.tcam': Mock()
        }
        self.module_patcher = patch.dict('sys.modules', mocked_modules)
        self.module_patcher.start()
        from monitor.microscope.microscope import Microscope   # noqa
        self.micro = Microscope()

    def tearDown(self):
        del self.micro
        self.mock_capture.reset_mock()
        self.mock_capture.Capture.reset_mock()
        self.mock_capture.Capture.side_effect = None
        self.module_patcher.stop()

    @patch.object(kernel, 'os_cmd')
    @patch.object(Pipeline, 'stage')
    def test_init(self, event_stage: MagicMock, os_cmd: MagicMock):
        """
        Test microscope channel and hardware initialization

        :param event_stage: [description]
        :type event_stage: MagicMock
        :param os_cmd: [description]
        :type os_cmd: MagicMock
        """
        # test bad uvcdynctrl init
        os_cmd.side_effect = OSError
        with self.assertRaises(UvcdynctrlError):
            self.micro.init()
        os_cmd.side_effect = None
        self.micro.fluorescence.initialize_hardware.side_effect = OSError
        with self.assertRaises(LightingError):
            self.micro.init()
        self.micro.fluorescence.initialize_hardware.side_effect = None
        self.micro.tcam.probe.side_effect = GSTDeviceError
        self.micro.init()
        self.micro.focus_stream_channel.construct.assert_not_called()
        self.micro.phase_capture_channel.construct.assert_not_called()
        self.micro.gfp_stream_channel.construct.assert_not_called()
        self.micro.gfp_capture_channel.construct.assert_not_called()
        self.micro.phase_stream_channel.construct.assert_not_called()
        self.micro.tcam.probe.side_effect = None
        self.micro.tcam.probe.return_value = Mock(), Mock()
        self.micro.init()
        self.micro.focus_stream_channel.construct.assert_called()
        self.micro.phase_capture_channel.construct.assert_called()
        self.micro.gfp_stream_channel.construct.assert_called()
        self.micro.gfp_capture_channel.construct.assert_called()
        self.micro.phase_stream_channel.construct.assert_called()
        event_stage.assert_has_calls([call(self.micro.capture, 1),
                                      call(self.micro.preview, 0)], any_order=False)

    @patch('monitor.microscope.microscope.Microscope.gfp_capture')
    @patch('monitor.microscope.microscope.Microscope.dpc_capture')
    @patch.object(StateManager, '__enter__')
    @patch.object(Event, 'trigger')
    def test_capture(self, trig: MagicMock, state: MagicMock, dpc_capture: MagicMock, gfp_capture: MagicMock):
        """[summary]

        :param trig: [description]
        :type trig: MagicMock
        :param state: [description]
        :type state: MagicMock
        :param dpc_capture: [description]
        :type dpc_capture: MagicMock
        :param gfp_capture: [description]
        :type gfp_capture: MagicMock
        """

        dpc_capture.return_value = Mock()
        state.return_value.imaging_profile.gfp_capture = False
        ret = self.micro.capture()
        dpc_capture.assert_called()
        gfp_capture.assert_not_called()
        trig.assert_has_calls([call(status=uis.STATUS_WORKING),
                              call(status=uis.STATUS_OK)], any_order=False)
        # make sure capture is sane
        self.mock_capture.Capture.assert_called_with(
            dpc_capture.return_value, state.return_value.imaging_profile.dpc_exposure, state.return_value.imaging_profile.gfp_capture)
        dpc_capture.reset_mock()
        self.mock_capture.Capture.reset_mock()
        trig.reset_mock()
        dpc_capture.return_value = ['dpc0', 'dpc1', 'dpc2', 'dpc3']
        gfp_capture.return_value = 'gfp'
        state.return_value.imaging_profile.gfp_capture = True
        ret = self.micro.capture()
        dpc_capture.assert_called()
        gfp_capture.assert_called()
        trig.assert_has_calls([call(status=uis.STATUS_WORKING),
                              call(status=uis.STATUS_OK)], any_order=False)
        # make sure capture is sane
        self.mock_capture.Capture.assert_called_with(
           ['dpc0', 'dpc1', 'dpc2', 'dpc3', 'gfp'], state.return_value.imaging_profile.dpc_exposure, state.return_value.imaging_profile.gfp_capture)

        dpc_capture.reset_mock()
        gfp_capture.reset_mock()
        trig.reset_mock()
        self.mock_capture.Capture.side_effect = TimeoutError
        with self.assertRaises(TimeoutError):
            ret = self.micro.capture()
        trig.assert_has_calls([call(status=uis.STATUS_WORKING),
                              call(status=uis.STATUS_ALERT)], any_order=False)

    @patch('monitor.microscope.microscope.Microscope.gfp_capture')
    @patch('monitor.microscope.microscope.Microscope.dpc_capture')
    @patch.object(StateManager, '__enter__')
    @patch.object(Event, 'trigger')
    def test_preview(self, trig: MagicMock, state: MagicMock, dpc_capture: MagicMock, gfp_capture: MagicMock):
        """
        Test preview capture method

        :param trig: [description]
        :type trig: MagicMock
        :param state: [description]
        :type state: MagicMock
        :param dpc_capture: [description]
        :type dpc_capture: MagicMock
        :param gfp_capture: [description]
        :type gfp_capture: MagicMock
        """
        dpc_capture.return_value = ['dpc0', 'dpc1', 'dpc2', 'dpc3']
        gfp_capture.return_value = 'gfp'
        # Without GFPs
        self.micro.preview(gfp=False)
        trig.assert_has_calls([call(status=uis.STATUS_WORKING),
                              call(status=uis.STATUS_OK)], any_order=False)
        self.mock_capture.Capture.assert_called_with(
            ['dpc0', 'dpc1', 'dpc2', 'dpc3'], state.return_value.imaging_profile.dpc_exposure, False)
        # With GFP
        self.micro.preview(gfp=True)
        self.mock_capture.Capture.assert_called_with(
            ['dpc0', 'dpc1', 'dpc2', 'dpc3', 'gfp'], state.return_value.imaging_profile.dpc_exposure, True)
        # Raises Timeout
        self.mock_capture.Capture.side_effect = TimeoutError
        with self.assertRaises(TimeoutError):
            ret = self.micro.preview()
        trig.assert_has_calls([call(status=uis.STATUS_WORKING),
                              call(status=uis.STATUS_ALERT)], any_order=False)

    @patch.object(time, 'sleep')
    @patch.object(ThreadManager, 'gst_bus_condition')
    def test_dpc_capture(self, tm: MagicMock, sleep: MagicMock):
        """
        Test dpc capture mechanism

        :param tm: [description]
        :type tm: MagicMock
        :param sleep: [description]
        :type sleep: MagicMock
        """
        self.micro.tcam.initialized = False
        with self.assertRaises(GSTDeviceError):
            self.micro.dpc_capture()
        self.micro.tcam.initialized = True
        self.micro.automatrix.initialized = False
        with self.assertRaises(LightingError):
            self.micro.dpc_capture()
        self.micro.automatrix.initialized = True
        self.micro.phase_capture_channel.initialized = False
        with self.assertRaises(ChannelError):
            self.micro.dpc_capture()
        self.micro.phase_capture_channel.initialized = True
        self.micro.tcam.dpc_light_exposure = 0.25  # type:ignore
        tm.wait.return_value = True
        self.micro.automatrix.dpc.patterns = [1, 2, 3, 4]
        sleep.reset_mock()
        self.micro.dpc_capture()
        sleep.assert_has_calls([call(0.25), call(0.25), call(0.25), call(0.25)])
        tm.wait.return_value = False
        self.micro.dpc_capture()

    @patch.object(time, 'sleep')
    @patch.object(ThreadManager, 'gst_bus_condition')
    def test_gfp_capture(self, tm: MagicMock, sleep: MagicMock):
        """
        Test gfp capture mechanism

        :param tm: [description]
        :type tm: MagicMock
        :param sleep: [description]
        :type sleep: MagicMock
        """
        self.micro.tcam.initialized = False
        with self.assertRaises(GSTDeviceError):
            self.micro.gfp_capture()
        self.micro.tcam.initialized = True
        self.micro.fluorescence.initialized = False
        with self.assertRaises(LightingError):
            self.micro.gfp_capture()
        self.micro.fluorescence.initialized = True
        self.micro.gfp_capture_channel.initialized = False
        with self.assertRaises(ChannelError):
            self.micro.gfp_capture()
        self.micro.gfp_capture_channel.initialized = True
        self.micro.tcam.gfp_light_exposure = 2  # type: ignore
        tm.wait.return_value = [1]
        self.micro.automatrix.dpc.patterns = [1]
        sleep.reset_mock()
        self.micro.gfp_capture()
        sleep.assert_called_once_with(2)
        tm.wait.return_value = None
        self.micro.gfp_capture()

    def test_exposure_stream_ctrl(self):
        """
        Test exposure stream control
        """
        self.micro.tcam.initialized = False
        with self.assertRaises(GSTDeviceError):
            self.micro.exposure_stream_ctrl(True)
        self.micro.tcam.initialized = True
        self.micro.automatrix.initialized = False
        with self.assertRaises(LightingError):
            self.micro.exposure_stream_ctrl(True)
        self.micro.automatrix.initialized = True
        self.micro.phase_stream_channel.initialized = False
        with self.assertRaises(ChannelError):
            self.micro.exposure_stream_ctrl(True)
        self.micro.phase_stream_channel.initialized = True
        self.micro.exposure_stream_ctrl(False)
        self.micro.automatrix.focus.patterns = [1]
        self.micro.exposure_stream_ctrl(True)

    def test_focus_stream_ctrl(self):
        """
        Test focus stream control
        """
        self.micro.tcam.initialized = False
        with self.assertRaises(GSTDeviceError):
            self.micro.focus_stream_ctrl(False)
        self.micro.tcam.initialized = True
        self.micro.automatrix.initialized = False
        with self.assertRaises(LightingError):
            self.micro.focus_stream_ctrl(False)
        self.micro.automatrix.initialized = True
        self.micro.phase_stream_channel.initialized = False
        with self.assertRaises(ChannelError):
            self.micro.focus_stream_ctrl(False)
        self.micro.phase_stream_channel.initialized = True
        self.micro.focus_stream_ctrl(False)
        self.micro.automatrix.focus.patterns = [1]
        self.micro.focus_stream_ctrl(True)

    def test_gfp_stream_ctrl(self):
        """
        Test gfp stream control
        """
        self.micro.tcam.initialized = False
        with self.assertRaises(GSTDeviceError):
            self.micro.gfp_stream_ctrl(False)
        self.micro.tcam.initialized = True
        self.micro.fluorescence.initialized = False
        with self.assertRaises(LightingError):
            self.micro.gfp_stream_ctrl(False)
        self.micro.fluorescence.initialized = True
        self.micro.gfp_stream_channel.initialized = False
        with self.assertRaises(ChannelError):
            self.micro.gfp_stream_ctrl(False)
        self.micro.gfp_stream_channel.initialized = True
        self.micro.gfp_stream_ctrl(False)
        self.micro.gfp_stream_ctrl(True)
