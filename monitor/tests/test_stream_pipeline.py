# -*- coding: utf-8 -*-
"""
Unittests for Stream Pipeline
=============================
Date: 2021-07

Dependencies:
-------------
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import asyncio
from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.state_manager import StateManager
import unittest
from unittest.mock import MagicMock, Mock, call, patch
from monitor.tests.resources import models
from monitor.environment.context_manager import ContextManager
from monitor.microscope.camera.properties.resolution import CMOSConfig


class TestStreamPipeline(unittest.TestCase):

    @patch.object(StateManager, 'subscribe')
    def setUp(self, subscribe: MagicMock):
        # mock numpy to prevent duplicate reload
        mocked_modules = {
            'gi': Mock(),
            'gi.repository': Mock(),
            'numpy': Mock(),
            'monitor.microscope.camera.gst_pipeline.GSTPipeline': Mock()
        }
        self.module_patcher = patch.dict('sys.modules', mocked_modules)
        self.module_patcher.start()
        from monitor.microscope.camera.stream_pipeline import StreamPipeline  # noqa
        self.stream_pipeline = StreamPipeline('test', False)

    def tearDown(self):
        self.module_patcher.stop()
        del self.stream_pipeline

    def test_initialized(self):
        """
        Test initialized property set
        """
        self.stream_pipeline.initialized = True
        self.assertTrue(self.stream_pipeline.initialized)

    @patch('monitor.microscope.camera.gst_pipeline.GSTPipeline.get_state')
    def test_update_profile(self, get_state: MagicMock) -> None:
        # test null state blocker
        get_state.return_value = self.stream_pipeline.null
        asyncio.run(self.stream_pipeline.update_profile(Mock()))
        self.stream_pipeline.source.set_tcam_property.assert_not_called()
        imaging_profile = Mock(spec=ImagingProfile)
        imaging_profile.configure_mock(**models.IMAGING_PROFILE_MODEL)
        # test dpc load
        get_state.return_value = self.stream_pipeline.playing
        self.stream_pipeline.gfp = False
        asyncio.run(self.stream_pipeline.update_profile(imaging_profile))
        self.stream_pipeline.source.set_tcam_property.assert_has_calls(
            [
                call("Exposure Time (us)", 8500),
                call("Gain", 4),
                call("Brightness", 168),
                call("Override Scanning Mode", 0)
            ],
            any_order=False
        )
        # test dpc load
        self.stream_pipeline.gfp = True
        asyncio.run(self.stream_pipeline.update_profile(imaging_profile))
        self.stream_pipeline.source.set_tcam_property.assert_has_calls(
            [
                call("Exposure Time (us)", 1050000),
                call("Gain", 60),
                call("Brightness", 168),
                call("Override Scanning Mode", 0)
            ],
            any_order=False
        )

    @patch.object(ContextManager, '__enter__', **{'return_value': Mock(spec=ContextManager)})
    def test_construct(self, context: MagicMock):
        """
        Mock all parent elements and run a pipeline construction
        """
        self.stream_pipeline.caps = Mock()
        self.stream_pipeline.queue = Mock()
        self.stream_pipeline.videoflip = Mock()
        self.stream_pipeline.sink = Mock()
        self.stream_pipeline.pipeline = Mock()
        self.stream_pipeline.source = Mock()
        self.stream_pipeline.convert = Mock()
        self.stream_pipeline.scale = Mock()
        self.stream_pipeline.caps_scale = Mock()
        self.stream_pipeline.img_buffer = Mock()
        resolution = Mock(spec=CMOSConfig)
        resolution.height = 400
        resolution.width = 400
        resolution.framerate = '1/4'
        self.stream_pipeline.construct(resolution)
