# -*- coding: utf-8 -*-
"""
Automatrix Unittests
====================
Modified: 2021-07

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import asyncio
import unittest
import logging
from unittest.mock import call, patch, Mock, MagicMock
from monitor.tests.resources import models, microscope
from monitor.environment.state_manager import StateManager
from monitor.microscope.automatrix.stream import AutomatrixStream
from monitor.models.imaging_profile import ImagingProfile
from monitor.microscope.automatrix.hardware import AutomatrixHardware


class TestAutomatrix(unittest.TestCase):

    @patch.object(AutomatrixStream, '__init__', lambda self: None)
    @patch.object(StateManager, 'subscribe')
    def setUp(self, subscribe: MagicMock):
        self.wiring_pi = Mock()
        self.mocked_modules = {
            'wiringpi': self.wiring_pi
        }
        self.module_patcher = patch.dict('sys.modules', self.mocked_modules)
        self.module_patcher.start()
        from monitor.microscope.automatrix.automatrix import Automatrix  # noqa
        logging.disable()
        self.automatrix = Automatrix()

    def tearDown(self):
        self.module_patcher.stop()
        del self.automatrix
        logging.disable(logging.NOTSET)

    @patch('monitor.microscope.automatrix.automatrix.Automatrix.enable')
    @patch('monitor.microscope.automatrix.automatrix.Automatrix.load_pattern')
    def test_del(self, load_pattern: MagicMock, enable: MagicMock):
        """
        Test delete method

        :param load_pattern: [description]
        :type load_pattern: MagicMock
        :param enable: [description]
        :type enable: MagicMock
        """
        self.automatrix.__del__()

    def test_focus(self):
        """
        Testing focus property set/get
        """
        self.automatrix.focus = focus_stream = Mock(spec=AutomatrixStream)
        self.assertEqual(focus_stream, self.automatrix.focus)

    def test_dpc(self):
        """
        Testing dpc property set/get
        """
        self.automatrix.dpc = dpc_stream = Mock(spec=AutomatrixStream)
        self.assertEqual(dpc_stream, self.automatrix.dpc)

    def test_outer_radius(self):
        """
        Testing outer radius property set/get
        """
        self.automatrix.outer_radius = 4.5
        self.assertEqual(4.5, self.automatrix.outer_radius)

    def test_inner_radius(self):
        """
        Testing inner radius property set/get
        """
        self.automatrix.inner_radius = 4.5
        self.assertEqual(4.5, self.automatrix.inner_radius)

    def test_initialized(self):
        """
        Testing initialized property set/get
        """
        self.assertFalse(self.automatrix.initialized)
        self.automatrix.outer_radius = 4.0
        self.automatrix.inner_radius = 3.0
        self.automatrix.dpc = Mock()
        self.automatrix.focus = Mock()
        self.assertTrue(self.automatrix.initialized)

    def test_initialize_hardware(self):
        """
        Test hardware initialization method
        """
        self.automatrix.initialize_hardware()
        self.wiring_pi.wiringPiSetupGpio.assert_called_once()
        self.wiring_pi.pinMode.assert_called_once_with(
            AutomatrixHardware.TRIGGER, self.wiring_pi.OUTPUT)
        self.wiring_pi.wiringPiSPISetup.assert_called_once_with(
            AutomatrixHardware.SPI_CHANNEL, AutomatrixHardware.SPI_SPEED)

    @patch('monitor.microscope.automatrix.automatrix.Automatrix.configure')
    def test_set_radius(self, configure: MagicMock):
        """
        Test set radius async subscribe

        :param configure: [description]
        :type configure: MagicMock
        """
        imaging_profile = Mock(spec=ImagingProfile)
        imaging_profile.configure_mock(**models.IMAGING_PROFILE_MODEL)
        # test cache hit inner and outer radius
        asyncio.run(self.automatrix.set_radius(imaging_profile))
        # test dpc inner/outer cache miss
        imaging_profile.dpc_inner_radius = 2.5
        asyncio.run(self.automatrix.set_radius(imaging_profile))

    @patch('monitor.microscope.automatrix.automatrix.Automatrix.enable')
    @patch('monitor.microscope.automatrix.automatrix.Automatrix._generate_dpc_patterns')
    @patch('monitor.microscope.automatrix.automatrix.Automatrix._generate_focus_pattern')
    def test_configure(self, focus: MagicMock, dpc: MagicMock, _: MagicMock):
        """
        Test automatrix configuration helper

        :param focus: [description]
        :type focus: MagicMock
        :param dpc: [description]
        :type dpc: MagicMock
        :param _: [description]
        :type _: MagicMock
        """
        self.automatrix.outer_radius = 4.0
        self.automatrix.inner_radius = 3.0
        self.automatrix.focus = Mock()
        self.automatrix.dpc = Mock()
        ptn1 = Mock()
        ptn2 = Mock()
        dpc.return_value = [ptn1, ptn2]
        self.automatrix.configure()
        focus.assert_called_once_with(self.automatrix.outer_radius, self.automatrix.inner_radius)
        self.automatrix.dpc.set_pattern.assert_has_calls(
            [
                call(ptn1),
                call(ptn2)
            ],
            any_order=False
        )

    def test_generate_dpc_patterns(self):
        """
        Test dpc pattern generation
        """
        self.automatrix.outer_radius = 4.0
        self.automatrix.inner_radius = 3.0
        self.automatrix._generate_dpc_patterns(
            self.automatrix.outer_radius, self.automatrix.inner_radius)

    def test_generate_focus_pattern(self):
        """
        Test focus pattern generation
        """
        self.automatrix.outer_radius = 4.0
        self.automatrix.inner_radius = 3.0
        self.automatrix._generate_focus_pattern(
            self.automatrix.outer_radius, self.automatrix.inner_radius)

    def test_enable(self):
        """
        Test enable helper
        """
        self.automatrix.enable(True)
        self.automatrix.elapsed_active = 4
        self.automatrix.enable(False)

    def test_load_pattern(self):
        """
        Test pattern loading helper
        """
        self.automatrix.load_pattern(microscope.DPC_PATTERN[1])
