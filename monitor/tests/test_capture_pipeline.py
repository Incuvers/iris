# -*- coding: utf-8 -*-
"""
Unittests for Capture Pipeline
==============================
Date: 2021-07

Dependencies:
-------------
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import os
import unittest
from typing import Optional
from unittest.mock import MagicMock, Mock, patch
from monitor.environment.context_manager import ContextManager
from monitor.microscope.camera.properties.resolution import CMOSConfig


class TestCapturePipeline(unittest.TestCase):

    def setUp(self):
        # mock numpy to prevent duplicate reload
        mocked_modules = {
            'gi': Mock(),
            'gi.repository': Mock(),
            'numpy': Mock(),
            'monitor.microscope.camera.gst_pipeline.GSTPipeline': Mock()
        }
        self.module_patcher = patch.dict('sys.modules', mocked_modules)
        self.module_patcher.start()
        from monitor.microscope.camera.capture_pipeline import CapturePipeline  # noqa
        self.capture_pipeline = CapturePipeline('test', False)

    def tearDown(self):
        self.module_patcher.stop()
        del self.capture_pipeline

    def test_initialized(self):
        """
        Test initialized property set
        """
        self.capture_pipeline.initialized = True
        self.assertTrue(self.capture_pipeline.initialized)

    @patch.object(ContextManager, '__enter__', **{'return_value': Mock(spec=ContextManager)})
    def test_construct(self, context: MagicMock):
        """
        Mock all parent elements and run a pipeline construction
        """
        context.return_value.get_env.side_effect = self.override
        self.capture_pipeline.caps = Mock()
        self.capture_pipeline.queue = Mock()
        self.capture_pipeline.videoflip = Mock()
        self.capture_pipeline.sink = Mock()
        self.capture_pipeline.pipeline = Mock()
        self.capture_pipeline.source = Mock()
        self.capture_pipeline.convert = Mock()
        self.capture_pipeline.img_buffer = Mock()
        resolution = Mock(spec=CMOSConfig)
        resolution.height = 400
        resolution.width = 400
        resolution.framerate = '1/4'
        self.capture_pipeline.construct(resolution)

    @staticmethod
    def override(args: str, _: str) -> Optional[str]:
        return os.environ.get(args)
