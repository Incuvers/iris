# -*- coding: utf-8 -*-
"""
Stream Pipeline
===============
Date: 2021-07

Dependencies:
-------------
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import gi  # type: ignore
import logging
import monitor.imaging.constants as ic
from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.state_manager import StateManager
from monitor.environment.context_manager import ContextManager
from monitor.microscope.camera.gst_pipeline import GSTPipeline
from monitor.microscope.camera.properties.resolution import CMOSConfig
# HACK: to fix lint E402
try:
    gi.require_version("Gst", "1.0")
finally:
    from gi.repository import Gst  # type: ignore


class StreamPipeline(GSTPipeline):

    def __init__(self, name: str, gfp: bool) -> None:
        self._logger = logging.getLogger(__name__)
        self.initialized = False
        super().__init__(name, gfp)
        with StateManager() as state:
            state.subscribe(ImagingProfile, self.update_profile)
        self._logger.debug("%s successfully instantiated", __name__)

    @property
    def initialized(self) -> bool:
        return self.__initialized

    @initialized.setter
    def initialized(self, status: bool) -> None:
        self.__initialized = status

    async def update_profile(self, imaging_profile: ImagingProfile) -> None:
        if self.get_state() is self.null:
            return
        # unpack current model settings
        exposure = imaging_profile.gfp_exposure if self.gfp else imaging_profile.dpc_exposure
        gain = imaging_profile.gfp_gain if self.gfp else imaging_profile.dpc_gain
        brightness = imaging_profile.gfp_brightness if self.gfp else imaging_profile.dpc_brightness
        scan_mode = ic.GFP_SCAN_MODE if self.gfp else ic.DPC_SCAN_MODE
        # set tcam properties
        self.source.set_tcam_property("Exposure Time (us)", exposure)
        self._logger.debug("%s: Successfully set tcam: %s to %s",
                           self.name, "Exposure Time (us)", exposure)
        self.source.set_tcam_property("Gain", gain)
        self._logger.debug("%s: Successfully set tcam: %s to %s", self.name, "Gain", gain)
        self.source.set_tcam_property("Brightness", brightness)
        self._logger.debug("%s: Successfully set tcam: %s to %s",
                           self.name, "Brightness", brightness)
        self.source.set_tcam_property("Override Scanning Mode", scan_mode)
        self._logger.debug("%s: Successfully set tcam: %s to %s",
                           self.name, "Override Scanning Mode", scan_mode)

    def construct(self, resolution: CMOSConfig):
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
        self.caps_scale.set_property("caps", Gst.Caps.from_string(
            "video/x-raw, width=884, height=724"))
        # tell appsink to notify us when it receives an image
        self.sink.set_property("emit-signals", True)
        self.sink.set_property('max-buffers', 10)
        self.sink.set_property("max-lateness", 1E7)
        # tell appsink what function to call when it notifies us
        self.sink.connect("new-sample", self.callback, self.img_buffer)
        # add pipeline elements
        self.pipeline.add(self.source)
        self.pipeline.add(self.caps)
        self.pipeline.add(self.videoflip)
        self.pipeline.add(self.queue)
        self.pipeline.add(self.convert)
        self.pipeline.add(self.scale)
        self.pipeline.add(self.caps_scale)
        self.pipeline.add(self.sink)
        self._logger.info("Completed adding %s elements", __name__)
        # link elements
        self.source.link(self.caps)
        self.caps.link(self.videoflip)
        self.videoflip.link(self.queue)
        self.queue.link(self.convert)
        self.convert.link(self.scale)
        self.scale.link(self.caps_scale)
        self.caps_scale.link(self.sink)
        self._logger.info("Completed linking %s elements", __name__)
        self.initialized = True
