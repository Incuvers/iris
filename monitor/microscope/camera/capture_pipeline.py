# -*- coding: utf-8 -*-
"""
Capture Pipeline
================
Date: 2021-07

Dependencies:
-------------
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import gi
import logging
from monitor.environment.context_manager import ContextManager
from monitor.microscope.camera.gst_pipeline import GSTPipeline
from monitor.microscope.camera.properties.resolution import CMOSConfig
# HACK: to fix lint E402
try:
    gi.require_version("Gst", "1.0")
finally:
    from gi.repository import Gst


class CapturePipeline(GSTPipeline):

    def __init__(self, name: str, gfp: bool) -> None:
        self._logger = logging.getLogger(__name__)
        self.initialized = False
        super().__init__(name, gfp)
        self._logger.debug("%s successfully instantiated", __name__)

    @property
    def initialized(self) -> bool:
        return self.__initialized

    @initialized.setter
    def initialized(self, status: bool) -> None:
        self.__initialized = status

    def construct(self, resolution: CMOSConfig) -> None:
        # create caps command string
        with ContextManager() as context:
            cmd_string = '{}, format={}, width={}, height={}, framerate={}'.format(
                context.get_env('TCAM_VIDEO_FORMAT', "video/x-raw"),
                context.get_env('TCAM_PIXEL_FORMAT', "GRAY8"),
                resolution.width,
                resolution.height,
                resolution.framerate
            )
        self.caps.set_property("caps", Gst.Caps.from_string(cmd_string))
        self.queue.set_property("max-size-buffers", 1)
        self.queue.set_property("flush-on-eos", True)
        self.videoflip.set_property("method", 'vertical-flip')
        self.sink.set_property('max-buffers', 1)
        self.sink.set_property("emit-signals", True)
        self.sink.connect("new-sample", self.callback, self.img_buffer)
        # add pipeline elements
        self.pipeline.add(self.source)
        self.pipeline.add(self.caps)
        self.pipeline.add(self.videoflip)
        self.pipeline.add(self.queue)
        self.pipeline.add(self.convert)
        self.pipeline.add(self.sink)
        self._logger.info("Completed adding %s elements", __name__)
        # link elements
        self.source.link(self.caps)
        self.caps.link(self.videoflip)
        self.videoflip.link(self.queue)
        self.queue.link(self.convert)
        self.convert.link(self.sink)
        self._logger.info("Completed linking %s elements", __name__)
        self.initialized = True
