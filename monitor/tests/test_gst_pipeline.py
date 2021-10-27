#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unittest for GST Pipeline
=========================
Date: 2021-04 

Dependencies:
-------------
```

```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import re
import gc
import numpy
import logging
import unittest

from threading import Condition
from unittest.mock import MagicMock, call, patch, Mock
from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.state_manager import StateManager
from monitor.tests.resources import microscope, models
from monitor.exceptions.microscope import GSTPipelineError


class TestGSTPipeline(unittest.TestCase):

    def setUp(self):
        self.gi = Mock()
        mocked_modules = {
            'gi': Mock(),
            'gi.repository': self.gi
        }
        self.module_patcher = patch.dict('sys.modules', mocked_modules)
        self.module_patcher.start()
        from monitor.microscope.camera.gst_pipeline import GSTPipeline  # noqa
        self.gi.Gst.ElementFactory.make.side_effect = self.element_make
        logging.disable()
        self.gst_pipeline = GSTPipeline(
            name=microscope.GST_NAME,
            gfp=False
        )

    def tearDown(self):
        self.module_patcher.stop()
        del self.gst_pipeline
        logging.disable(logging.NOTSET)

    def test_pipeline_init_error(self):
        from monitor.microscope.camera.gst_pipeline import GSTPipeline  # noqa
        self.gi.Gst.init_check.return_value = False
        with self.assertRaises(GSTPipelineError):
            _ = GSTPipeline(
                name=microscope.GST_NAME,
                gfp=False
            )

    @patch.object(Condition, 'wait')
    @patch('monitor.microscope.camera.gst_pipeline.GSTPipeline.gst_bus_loop')
    @patch('monitor.microscope.camera.gst_pipeline.GSTPipeline.load_properties')
    def test_start(self, load_properties: MagicMock, gst_bus_loop: MagicMock, wait: MagicMock):
        self.gst_pipeline.start()
        self.gst_pipeline.pipeline.set_state.assert_called_with(self.gst_pipeline.playing)

    @patch.object(gc, 'collect')
    def test_stop(self, collect: MagicMock):
        self.gst_pipeline.stop()
        self.gst_pipeline.pipeline.set_state.assert_called_with(self.gst_pipeline.null)

    def test_get_state(self):
        self.gst_pipeline.pipeline.get_state.return_value.state = self.gst_pipeline.playing
        self.assertEqual(self.gst_pipeline.get_state(), self.gst_pipeline.playing)

    @patch('monitor.microscope.camera.gst_pipeline.GSTPipeline.get_state')
    @patch.object(StateManager, '__enter__', return_value=Mock(spec=StateManager))
    def test_load_properties(self, state: MagicMock, get_state: MagicMock):
        # test null state blocker
        get_state.return_value = self.gst_pipeline.null
        self.gst_pipeline.load_properties()
        self.gst_pipeline.source.set_tcam_property.assert_not_called()
        state.return_value.imaging_profile = Mock(spec=ImagingProfile)
        state.return_value.imaging_profile.configure_mock(**models.IMAGING_PROFILE_MODEL)
        # test dpc load
        get_state.return_value = self.gst_pipeline.playing
        self.gst_pipeline.gfp = False
        self.gst_pipeline.load_properties()
        self.gst_pipeline.source.set_tcam_property.assert_has_calls(
            [
                call("Exposure Time (us)", 8500),
                call("Gain", 4),
                call("Brightness", 168),
                call("Override Scanning Mode", 0)
            ],
            any_order=False
        )
        # test dpc load
        self.gst_pipeline.gfp = True
        self.gst_pipeline.load_properties()
        self.gst_pipeline.source.set_tcam_property.assert_has_calls(
            [
                call("Exposure Time (us)", 1050000),
                call("Gain", 60),
                call("Brightness", 168),
                call("Override Scanning Mode", 0)
            ],
            any_order=False
        )

    @patch.object(re, 'search')
    @patch.object(Condition, 'notify_all', lambda x: None)
    def test_bus_callback(self, search: MagicMock):
        message = Mock()
        # test EOS signal
        message.type = self.gi.Gst.MessageType.EOS
        self.assertTrue(self.gst_pipeline.bus_callback(Mock(), message, Mock()))
        self.gst_pipeline.loop.quit.assert_called()
        # test state change
        message.type = self.gi.Gst.MessageType.STATE_CHANGED
        message.src.name = 'pipeline'
        message.parse_state_changed.return_value = self.gst_pipeline.paused, self.gst_pipeline.playing, Mock()
        self.assertTrue(self.gst_pipeline.bus_callback(Mock(), message, Mock()))
        message.parse_state_changed.return_value = self.gst_pipeline.null, self.gst_pipeline.ready, Mock()
        self.assertTrue(self.gst_pipeline.bus_callback(Mock(), message, Mock()))
        # test state change
        message.type = self.gi.Gst.MessageType.WARNING
        message.parse_warning.return_value = Mock(), Mock()
        self.assertTrue(self.gst_pipeline.bus_callback(Mock(), message, Mock()))
        message.parse_warning.assert_called()
        # test error
        message.type = self.gi.Gst.MessageType.ERROR
        message.src.get_name.return_value = "tcamsrc"
        err = Mock()
        err.message.startswith.return_value = True
        message.parse_error.return_value = err, Mock()
        self.assertTrue(self.gst_pipeline.bus_callback(Mock(), message, Mock()))
        self.gst_pipeline.loop.quit.assert_called()

    @patch.object(numpy, 'ndarray')
    @patch.object(numpy, 'array')
    def test_callback(self, array: MagicMock, ndarray: MagicMock):
        appsink = Mock()
        queue = Mock()
        # test no sample pull
        appsink.emit.return_value = None
        self.assertEqual(self.gst_pipeline.callback(appsink, queue), self.gi.Gst.FlowReturn.OK)
        queue.append.assert_not_called()
        # test no sample pull
        sample = Mock()
        sample.get_caps.return_value = (Mock(), Mock())
        sample.get_buffer.return_value.map.return_value = (Mock(), Mock())
        appsink.emit.return_value = sample
        self.assertEqual(self.gst_pipeline.callback(appsink, queue), self.gi.Gst.FlowReturn.OK)
        queue.append.assert_called()

    def test_construct(self):
        with self.assertRaises(NotImplementedError):
            self.gst_pipeline.construct(Mock())

    def element_make(self, _type: str, name: str) -> Mock:
        if _type == "tcamsrc":
            self.source = Mock()
            return self.source
        if _type == "capsfilter":
            self.caps = Mock()
            return self.caps
        if _type == "queue":
            self.queue = Mock()
            return self.queue
        if _type == "videoconvert":
            self.convert = Mock()
            return self.convert
        if _type == "videoflip":
            self.videoflip = Mock()
            return self.videoflip
        if _type == "videoscale":
            self.scale = Mock()
            return self.scale
        if _type == "" and name == microscope.GST_NAME + "-caps-scale":
            self.caps_scale = Mock()
            return self.caps_scale
        self.sink = Mock()
        return self.sink
