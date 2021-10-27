#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GST Pipeline
============
Modified: 2020-09

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import gi
import re
import gc
import logging
import numpy as np
from collections import deque
from threading import Condition
import monitor.imaging.constants as ic
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.exceptions.microscope import GSTPipelineError
from monitor.microscope.camera.properties.resolution import CMOSConfig

# HACK: to fix lint E402
try:
    gi.require_version("Gst", "1.0")
    gi.require_version("GstVideo", "1.0")
    gi.require_version("Tcam", "0.1")
finally:
    from gi.repository import Gst, GLib, Tcam  # type: ignore


class GSTPipeline:

    TIMEOUT = 5

    def __init__(self, name: str, gfp: bool):
        self.loop = GLib.MainLoop()
        self._logger = logging.getLogger(__name__)
        # thread notifier for safe pipeline state for property setting
        self.property_condition = Condition()
        # HACK: to fix lint F401
        self._logger.debug(Tcam)
        self.name = name
        self.gfp = gfp
        if not Gst.init_check(''):
            self._logger.error("Failed to initialize gst instance")
            raise GSTPipelineError
        # self.trigger_mode = False
        # using deque for faster pop operations for fixed sized elements
        self.img_buffer: deque[np.ndarray] = deque(maxlen=5)
        self.playing = Gst.State.PLAYING
        self.paused = Gst.State.PAUSED
        self.null = Gst.State.NULL
        self.ready = Gst.State.READY
        # TODO: pipe debug output to prod
        # Gst.debug_set_active(True)  # show debugging
        # Gst.debug_set_default_threshold(4)  # choose debugging message level
        self.pipeline = Gst.Pipeline("pipeline")
        self.source = Gst.ElementFactory.make("tcamsrc", name + "-src")
        self.caps = Gst.ElementFactory.make("capsfilter", name + "-caps")
        self.queue = Gst.ElementFactory.make('queue', name + "-queue")
        self.convert = Gst.ElementFactory.make("videoconvert", name + "-videoconvert")
        self.videoflip = Gst.ElementFactory.make("videoflip", name + "-videoflip")
        self.scale = Gst.ElementFactory.make("videoscale", name + "-videoscale")
        self.caps_scale = Gst.ElementFactory.make("capsfilter", name + "-caps-scale")
        # make sink elem
        self.sink = Gst.ElementFactory.make('appsink', name + "-appsink")
        self.bus = self.pipeline.get_bus()
        # configure bus for error handling and bus monitoring
        self.bus.add_signal_watch()
        self.bus.enable_sync_message_emission()
        self.bus.connect('message', self.bus_callback, None)
        self._logger.debug("Pipeline bus configured.")
        self.pipeline.set_auto_flush_bus(True)
        self._logger.debug("Pipeline auto flush set to: %s", self.pipeline.get_auto_flush_bus())

    def construct(self, resolution: CMOSConfig) -> None:
        raise NotImplementedError

    def start(self):
        """
        Sets the pipeline to the PLAYING state and enables the software trigger mode if
        the pipeline is set in capture mode.

        :raises TimeoutError:
        """
        self.pipeline.set_state(self.playing)
        self._logger.debug("%s GST pipeline set to PLAYING.", self.name)
        self.gst_bus_loop()
        # be notified when new messages occur.
        # load local camera properties only when the stream is playing
        with self.property_condition:
            self.property_condition.wait(timeout=self.TIMEOUT)
            self.load_properties()

    def stop(self):
        """
        Stop the pipeline This emits a End-of-Signal event from the source before settings the state to NULL. Note that
        signals sent to the pipeline with the `valve(drop=True)` will not reach the HDMIsink, so the HDMIvalve will be
        opened `valve(drop=False)` to let the signal reach the sink.

        :raises TimeoutError:
        """
        self.loop.quit()
        self.pipeline.set_state(self.null)
        self.active = False
        self._logger.debug("%s GST pipeline set to NULL.", self.name)
        self.img_buffer.clear()
        self._logger.debug("Image buffer cleared.")
        gc.collect()
        self._logger.debug("Garbage collection completed.")

    @tm.threaded(daemon=True)
    def gst_bus_loop(self):
        self._logger.debug("Starting gst bus listener")
        self.loop.run()

    def get_state(self):
        """
        Get current pipeline state

        :returns: the Gst state of the pipline
        """
        return self.pipeline.get_state(1).state

    def load_properties(self) -> None:
        """
        Updates all tcam properties for inbound capture or streaming mode
        Example of property_def: (True, value=80000, min=100, max=30000000, def=33333, step=1,
        type='integer', flags=0, category='Unknown', group='INVALID_PORPERTY')

        :raises TypeError: if the property cannot be found or if pipeline state is not valid
        """
        if self.get_state() is self.null:
            return
        # prevalidated
        with StateManager() as state:
            imaging_profile = state.imaging_profile
        # check if imaging profile state is initialized
        if not imaging_profile.initialized:
            self._logger.warning("Imaging Profile state model not initialized, skipping")
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

    def bus_callback(self, bus, message, user_data):
        """
        Gstreamer Message Types and how to parse
        https://lazka.github.io/pgi-docs/Gst-1.0/flags.html#Gst.MessageType
        """
        mtype = message.type
        src = message.src.name
        if mtype == Gst.MessageType.EOS:
            # end-of-stream
            self._logger.debug("%s: GST element %s detected an end of stream.", self.name, src)
            self.loop.quit()
        elif src == 'pipeline' and mtype == Gst.MessageType.STATE_CHANGED:
            old, new, _ = message.parse_state_changed()
            self._logger.debug(
                "%s: GST element %s state was changed to: %s, from: %s", self.name, src, new, old)
            # if PAUSED -> PLAYING notify of playing
            if old == self.paused and new == self.playing:
                with tm.gst_bus_condition:
                    tm.gst_bus_condition.notify_all()
                    self._logger.debug("Notified playing condition threads")
            elif old == self.null and new == self.ready:
                with self.property_condition:
                    self.property_condition.notify_all()
                    self._logger.debug("Notified ready condition threads")
        elif mtype == Gst.MessageType.ERROR:
            # Handle Errors
            err, _ = message.parse_error()
            self._logger.error("%s: GST element %s GST error was issued: %s", self.name, src, err)
            # if you use tcamsrc directly this will be the name you give to the element
            # if (strcmp(source_name, "tcamsrc0") == 0)
            if message.src.get_name() == "tcamsrc":
                if err.message.startswith("Device lost ("):
                    m = re.search(r'Device lost \((.*)\)', err.message)
                    self._logger.error(
                        "%s: Device lost came from device with serial: %s", self.name, m.group(1))  # type: ignore
                    # device lost handling should be initiated here
                    # this example simply stops playback
                    self.loop.quit()
        elif mtype == Gst.MessageType.WARNING:
            # Handle warnings
            err, _ = message.parse_warning()
            self._logger.warning("%s: a GST warning was issued: %s", self.name, err)
        return True

    @staticmethod
    def callback(appsink, queue: deque):
        """
        This function will be called in a separate thread when appsink is either triggered
        through a software trigger or is set to emit when data is in the buffer.
        """
        sample = appsink.emit("pull-sample")
        if sample:
            caps = sample.get_caps()
            gst_buffer = sample.get_buffer()
            buffer_map = None
            try:
                width = caps[0].get_value("width")
                height = caps[0].get_value("height")
                _, buffer_map = gst_buffer.map(Gst.MapFlags.READ)
                data = gst_buffer.extract_dup(0, gst_buffer.get_size())
                capture = np.array([])
                capture = np.ndarray((height, width, 1), buffer=data, dtype=np.uint8)
                # write to callback
                queue.append(capture)
            finally:
                gst_buffer.unmap(buffer_map)
        return Gst.FlowReturn.OK
