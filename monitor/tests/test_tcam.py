# -*- coding: utf-8 -*-
"""
Unittests for Tcam
==================
Date: 2021-07

Dependencies:
-------------
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import copy
import logging
import unittest
from unittest.mock import MagicMock, Mock, patch
from monitor.models.imaging_profile import ImagingProfile
from monitor.tests.resources import microscope, models
from monitor.exceptions.microscope import GSTDeviceError, MultipleGSTDevicesError, NoGSTDeviceError, PropertyError
from monitor.environment.state_manager import StateManager
from monitor.environment.context_manager import ContextManager
from monitor.microscope.camera.properties.resolution import CMOSConfig


class ValueList:

    @classmethod
    def get_size(cls, *args, **kwargs) -> int:
        return 1

    @classmethod
    def get_value(cls, *args, **kwargs) -> str:
        return "1/2"


class TestTcamProperties(unittest.TestCase):

    @patch.object(CMOSConfig, '__init__', lambda w, x, y, z: None)
    @patch.object(StateManager, 'subscribe')
    @patch.object(ContextManager, '__enter__', **{'return_value': Mock(spec=ContextManager)})
    def setUp(self, context: MagicMock, subscribe: MagicMock):
        self.gi = Mock()
        mocked_modules = {
            'gi': Mock(),
            'gi.repository': self.gi
        }
        self.module_patcher = patch.dict('sys.modules', mocked_modules)
        self.module_patcher.start()
        from monitor.microscope.camera.properties.tcam import TcamProperties  # noqa
        logging.disable()
        self.tcam = TcamProperties()
        self.tcam.video = microscope.TCAM_VIDEO_FORMAT
        self.tcam.fmt = microscope.TCAM_PIXEL_FORMAT

    def tearDown(self):
        self.module_patcher.stop()
        del self.tcam
        logging.disable(logging.NOTSET)

    def test_repr(self):
        self.tcam.__repr__()

    def test_setgetattrs(self):
        """
        Test Tcam Properties getter and setters
        """
        self.tcam.setattrs(**microscope.TCAM_PROPERTIES)
        self.assertDictEqual(self.tcam.getattrs(), microscope.TCAM_PROPERTIES)

    @patch.object(StateManager, '__enter__')
    @patch.object(CMOSConfig, '__init__', lambda self, name, resolution, framerate: None)
    @patch('monitor.microscope.camera.properties.tcam.TcamProperties.get_hardware_properties')
    def test_probe(self, get_hardware_properties: MagicMock, state: MagicMock):
        """
        """
        # test sanity
        get_hardware_properties.return_value = (
            microscope.TCAM_PROPERTIES['model'],
            microscope.TCAM_PROPERTIES['serial'],
            microscope.TCAM_PROPERTIES['identifier'],
            microscope.TCAM_PROPERTIES['backend'],
            microscope.TCAM_PROBE,
            microscope.TCAM_CAPS
        )
        self.tcam.probe()
        # test bad property
        bad_tcam_probe = copy.deepcopy(microscope.TCAM_PROBE)
        bad_tcam_probe.pop('Brightness')
        get_hardware_properties.return_value = (
            microscope.TCAM_PROPERTIES['model'],
            microscope.TCAM_PROPERTIES['serial'],
            microscope.TCAM_PROPERTIES['identifier'],
            microscope.TCAM_PROPERTIES['backend'],
            bad_tcam_probe,
            microscope.TCAM_CAPS
        )
        with self.assertRaises(PropertyError):
            self.tcam.probe()

    def test_validator(self):
        """
        Test validator function
        """
        imaging_profile = Mock(spec=ImagingProfile)
        imaging_profile.configure_mock(**models.IMAGING_PROFILE_MODEL)
        # populate ranges
        self.tcam.exposure_range = microscope.TCAM_PROBE['Exposure Time (us)']['min'], microscope.TCAM_PROBE[
            'Exposure Time (us)']['max']
        self.tcam.gain_range = microscope.TCAM_PROBE['Gain']['min'], microscope.TCAM_PROBE['Gain']['max']
        self.tcam.brightness_range = (
            microscope.TCAM_PROBE['Brightness']['min'], microscope.TCAM_PROBE['Brightness']['max'])

        self.assertTrue(self.tcam.validator(imaging_profile))
        # test bad dpc gain
        temp = imaging_profile.dpc_gain
        imaging_profile.dpc_gain = -8
        self.assertFalse(self.tcam.validator(imaging_profile))
        imaging_profile.dpc_gain = temp
        # test bad gfp gain
        temp = imaging_profile.gfp_gain
        imaging_profile.gfp_gain = -2
        self.assertFalse(self.tcam.validator(imaging_profile))
        imaging_profile.gfp_gain = temp
        # test bad dpc exposure
        temp = imaging_profile.dpc_exposure
        imaging_profile.dpc_exposure = -2
        self.assertFalse(self.tcam.validator(imaging_profile))
        imaging_profile.dpc_exposure = temp
        # test bad dpc exposure
        temp = imaging_profile.gfp_exposure
        imaging_profile.gfp_exposure = -2
        self.assertFalse(self.tcam.validator(imaging_profile))
        imaging_profile.gfp_exposure = temp
        # test bad gfp brightness
        temp = imaging_profile.gfp_brightness
        imaging_profile.gfp_brightness = -2
        self.assertFalse(self.tcam.validator(imaging_profile))
        imaging_profile.gfp_brightness = temp
        # test bad dpc brightness
        temp = imaging_profile.dpc_brightness
        imaging_profile.dpc_brightness = -2
        self.assertFalse(self.tcam.validator(imaging_profile))
        imaging_profile.dpc_brightness = temp

    def test_initialized(self):
        self.tcam.initialized = True
        self.assertTrue(self.tcam.initialized)

    def test_max(self):
        _max = Mock(spec=CMOSConfig)
        self.tcam.max = _max
        self.assertEqual(self.tcam.max, _max)

    def test_ultra(self):
        _ultra = Mock(spec=CMOSConfig)
        self.tcam.ultra = _ultra
        self.assertEqual(self.tcam.ultra, _ultra)

    def test_high(self):
        _high = Mock(spec=CMOSConfig)
        self.tcam.high = _high
        self.assertEqual(self.tcam.high, _high)

    def test_medium(self):
        _medium = Mock(spec=CMOSConfig)
        self.tcam.medium = _medium
        self.assertEqual(self.tcam.medium, _medium)

    def test_low(self):
        _low = Mock(spec=CMOSConfig)
        self.tcam.low = _low
        self.assertEqual(self.tcam.low, _low)

    def test_scan_modes(self):
        self.assertEqual(self.tcam.scan_modes, [0, 1, 2, 3, 4])

    def test_gfp_light_exposure(self):
        self.assertEqual(self.tcam.gfp_light_exposure, 2)

    def test_dpc_light_exposure(self):
        self.assertEqual(self.tcam.dpc_light_exposure, 0.25)

    def test_model(self):
        self.tcam.model = "Test"
        self.assertEqual(self.tcam.model, "Test")

    def test_serial(self):
        self.tcam.serial = "Test"
        self.assertEqual(self.tcam.serial, "Test")

    def test_identifier(self):
        self.tcam.identifier = "Test"
        self.assertEqual(self.tcam.identifier, "Test")

    def test_backend(self):
        self.tcam.backend = "Test"
        self.assertEqual(self.tcam.backend, "Test")

    def test_get_hardware_properties(self):
        # test bad gst init
        self.gi.Gst.init_check.return_value = False
        with self.assertRaises(GSTDeviceError):
            self.tcam.get_hardware_properties()
        self.gi.Gst.init_check.return_value = True
        # test no devices
        self.gi.Gst.ElementFactory.make.return_value.get_device_serials.return_value = []
        with self.assertRaises(NoGSTDeviceError):
            self.tcam.get_hardware_properties()
        # test multiple devices
        self.gi.Gst.ElementFactory.make.return_value.get_device_serials.return_value = [
            object(), object()]
        with self.assertRaises(MultipleGSTDevicesError):
            self.tcam.get_hardware_properties()
        # test bad device status
        self.gi.Gst.ElementFactory.make.return_value.get_device_serials.return_value = [Mock()]
        self.gi.Gst.ElementFactory.make.return_value.get_device_info.return_value = (
            False, "", "", "")
        with self.assertRaises(PropertyError):
            self.tcam.get_hardware_properties()
        # test bad property set
        self.gi.Gst.ElementFactory.make.return_value.get_device_serials.return_value = [Mock()]
        self.gi.Gst.ElementFactory.make.return_value.get_device_info.return_value = (
            True, "", "", "")
        self.gi.Gst.ElementFactory.make.return_value.get_tcam_property_names.return_value = ['Gain']
        self.gi.Gst.ElementFactory.make.return_value.get_static_pad.return_value.query_caps.return_value.get_structure.side_effect = TypeError
        self.gi.Gst.ElementFactory.make.return_value.get_static_pad.return_value.query_caps.return_value.get_size.return_value = 1
        self.gi.Gst.ElementFactory.make.return_value.get_tcam_property.return_value = (
            True, '', 0, 100, '', '', '', '', '', '')
        with self.assertRaises(PropertyError):
            self.tcam.get_hardware_properties()
        self.gi.Gst.ElementFactory.make.return_value.get_static_pad.return_value.query_caps.return_value.get_structure.side_effect = None
        # test name for loop
        self.gi.Gst.ElementFactory.make.return_value.get_device_info.return_value = (
            True, "", "", "")
        self.gi.Gst.ElementFactory.make.return_value.get_tcam_property_names.return_value = ['Gain']
        self.gi.Gst.ElementFactory.make.return_value.get_static_pad.return_value.query_caps.return_value.get_size.return_value = 1
        self.gi.Gst.ElementFactory.make.return_value.get_tcam_property.return_value = (
            True, '', 0, 100, '', '', '', '', '', '')
        self.gi.Gst.ElementFactory.make.return_value.get_static_pad.return_value.query_caps.return_value.get_structure.return_value.get_value.return_value = ValueList()
        self.gi.Gst.ValueList = ValueList
        self.tcam.get_hardware_properties()
