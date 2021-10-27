# -*- coding: utf-8 -*-
"""
Microscope
==========
Modified: 2021-07

This class is responsible for sequencing camera and lighting interfaces in order to stream and
capture cell images.

Dependencies:
-------------
```
import time
import logging
import numpy as np
from typing import List
from monitor.sys import kernel
from monitor.imaging.capture import Capture
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.context_manager import ContextManager
from monitor.microscope.camera.properties.tcam import TcamProperties
from monitor.microscope.camera.capture_pipeline import CapturePipeline
from monitor.microscope.camera.stream_pipeline import StreamPipeline
from monitor.microscope.fluorescence.fluorescence import Fluorescence
from monitor.microscope.automatrix.automatrix import Automatrix
from monitor.exceptions.microscope import ChannelError, GSTDeviceError, LightingError, UvcdynctrlError
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import time
import logging
import numpy as np
from typing import List
from monitor.sys import kernel
from monitor.imaging.capture import Capture
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.context_manager import ContextManager
from monitor.microscope.camera.properties.tcam import TcamProperties
from monitor.microscope.camera.capture_pipeline import CapturePipeline
from monitor.microscope.camera.stream_pipeline import StreamPipeline
from monitor.microscope.fluorescence.fluorescence import Fluorescence
from monitor.microscope.automatrix.automatrix import Automatrix
from monitor.exceptions.microscope import ChannelError, GSTDeviceError, LightingError, UvcdynctrlError


class Microscope:

    # 5 second timeout for stream ready
    BUS_TIMEOUT = 5
    _logger = logging.getLogger(__name__)
    # shared instances
    tcam = TcamProperties()
    automatrix = Automatrix()
    fluorescence = Fluorescence()
    focus_stream_channel = StreamPipeline(name='focus', gfp=False)
    phase_stream_channel = StreamPipeline(name='phase', gfp=False)
    gfp_stream_channel = StreamPipeline(name='gfp', gfp=True)
    gfp_capture_channel = CapturePipeline(name='gfp', gfp=True)
    phase_capture_channel = CapturePipeline(name='phase', gfp=False)

    @classmethod
    def init(cls):
        # initialize uvcdynctrl catch errors and report hardware init failure
        # NOTE: we can still have NoneType properties returned by the hardware properties if, for example
        # init_uvc fails, as a result we need to implement a deeper handling process for this case
        try:
            kernel.os_cmd(
                "$SNAP/usr/bin/uvcdynctrl\
                -i $SNAP/usr/share/uvcdynctrl/data/199e/usb3.xml\
                -d /dev/video0"
            )
        except OSError as exc:
            cls._logger.critical("Failed to initialize uvcdynctrl. Command failed with message: %s \
                and exit status: %s", exc.strerror, exc.errno)
            # only raise UVC error if in production environment
            with ContextManager() as context:
                if not context.get_env('MONITOR_ENV') == "development":
                    raise UvcdynctrlError from exc
        try:
            # Configure Fluorescence hardware
            cls.fluorescence.initialize_hardware()
            # Configure Automatrix hardware
            cls.automatrix.initialize_hardware()
        except BaseException as exc:
            cls._logger.critical(
                "An error occured while initializing microscope lighting hardware: %s", exc)
            raise LightingError from exc
        cls.tcam = TcamProperties()
        try:
            med, ultra = cls.tcam.probe()
        except GSTDeviceError as exc:
            cls._logger.critical("tcam hardware probe failed: %s", exc)
        else:
            cls.focus_stream_channel.construct(resolution=med)
            cls.phase_stream_channel.construct(resolution=ultra)
            cls.gfp_stream_channel.construct(resolution=ultra)
            cls.gfp_capture_channel.construct(resolution=ultra)
            cls.phase_capture_channel.construct(resolution=ultra)
        events.capture_pipeline.stage(cls.capture, 1)
        events.preview_pipeline.stage(cls.preview, 0)
        cls._logger.info("Microscope initialization successful")

    @classmethod
    def capture(cls) -> Capture:
        """
        Perform an imaging capture
        """
        capture = None
        events.system_status.trigger(status=uis.STATUS_WORKING)
        with StateManager() as state:
            imaging_profile = state.imaging_profile
        cls._logger.debug("Executing capture using %s", imaging_profile)
        try:
            # in experiment mode use gfp object reference
            cls._logger.debug("Executing DPC capture")
            components = cls.dpc_capture()
            cls._logger.info("DPC capture complete @ exposure: %s", imaging_profile.dpc_exposure)
            # if active imaging profile is gfp perform gfp capture
            if imaging_profile.gfp_capture:
                cls._logger.debug("Executing GFP capture")
                gfp_capture = cls.gfp_capture()
                # link gfp capture to dpc components which will make it a list of length 5 instead of 4 captures
                components.append(gfp_capture)
                cls._logger.debug("GFP capture complete @ exposure: %s",
                                  imaging_profile.gfp_exposure)
            # create capture object for encapsulation
            capture = Capture(components, imaging_profile.dpc_exposure,
                              imaging_profile.gfp_capture)
        except TimeoutError as exc:
            cls._logger.exception("A timeout occurred when capturing image")
            events.system_status.trigger(status=uis.STATUS_ALERT)
            raise exc
        else:
            events.system_status.trigger(status=uis.STATUS_OK)
        return capture

    @classmethod
    def preview(cls, gfp: bool = False) -> Capture:
        """
        Perform a preview capture with the active imaging profile settings except that the gfp flag overrides the
        active imaging profiles gfp setting

        :param gfp: dpc or gfp preview mode
        """
        capture = None
        events.system_status.trigger(status=uis.STATUS_WORKING)
        with StateManager() as state:
            imaging_profile = state.imaging_profile
        try:
            cls._logger.debug("Executing instant preview DPC capture")
            components = cls.dpc_capture()
            cls._logger.info("DPC capture complete @ exposure: %s", imaging_profile.dpc_exposure)
            # in instant preview mode we override the active imaging profile gfp setting
            if gfp:
                cls._logger.debug("Executing instant preview GFP capture")
                gfp_capture = cls.gfp_capture()
                # link gfp capture to dpc components which will make it a list of length 5 instead of 4 captures
                components.append(gfp_capture)
                cls._logger.debug("GFP capture complete @ exposure: %s",
                                  imaging_profile.gfp_exposure)
            # create capture object for encapsulation
            capture = Capture(components, imaging_profile.dpc_exposure, gfp)
        except TimeoutError as exc:
            cls._logger.exception("An exception occurred when capturing image")
            events.system_status.trigger(status=uis.STATUS_ALERT)
            raise exc
        else:
            events.system_status.trigger(status=uis.STATUS_OK)
        return capture

    @classmethod
    def dpc_capture(cls) -> List[np.ndarray]:
        """
        Captures a sequence of DPC images and store in dpc buffer.

        :raises GSTDeviceError: if GST device fails to initialize
        :raises LightingError: if the required lighting module is not initialized
        :raises ChannelError: if the required channel is not initialized
        :return: phase components 
        :rtype: List[np.ndarray]
        """
        if not cls.tcam.initialized:
            raise GSTDeviceError
        if not cls.automatrix.initialized:
            raise LightingError
        if not cls.phase_capture_channel.initialized:
            raise ChannelError
        # clear any existing components
        _dpc_buffer = []
        exposure_time = cls.tcam.dpc_light_exposure
        cls.phase_capture_channel.start()
        # block until stream notifier
        with tm.gst_bus_condition:
            result = tm.gst_bus_condition.wait(timeout=cls.BUS_TIMEOUT)
        # timeout handler
        if result:
            # iterate through DPC automatrix stream patterns
            for pattern in cls.automatrix.dpc.patterns:
                # load the first pattern into the shift registers
                cls.automatrix.load_pattern(pattern)
                cls.automatrix.enable(True)
                cls._logger.debug("Starting exposure sleep time")
                time.sleep(exposure_time)
                cls._logger.debug("Extracting sample")
                try:
                    img = cls.phase_capture_channel.img_buffer.pop()
                except IndexError:
                    cls._logger.error("Image buffer empty on request. Retrying sample extraction in: %s", exposure_time)
                    time.sleep(exposure_time)
                    img = cls.phase_capture_channel.img_buffer.pop()
                else:
                    cls._logger.debug("Sample acquired")
                    _dpc_buffer.append(img)
                finally:
                    # disable automatrix for next pattern load
                    cls.automatrix.enable(False) 
        else:
            cls._logger.warning("DPC stream timed out. Returning zeros matrix")
            _dpc_buffer = [np.zeros((1920, 2560, 1)) for _ in range(4)]
        cls.phase_capture_channel.stop()
        return _dpc_buffer

    @classmethod
    def gfp_capture(cls) -> np.ndarray:
        """
        Captures a single GFP image and store in gfp buffer.

        :raises GSTDeviceError: if GST device fails to initialize
        :raises LightingError: if the required lighting module is not initialized
        :raises ChannelError: if the required channel is not initialized
        :return: GFP capture
        :rtype: np.ndarray
        """
        if not cls.tcam.initialized:
            raise GSTDeviceError
        if not cls.fluorescence.initialized:
            raise LightingError
        if not cls.gfp_capture_channel.initialized:
            raise ChannelError
        img: np.ndarray
        exposure_time = cls.tcam.gfp_light_exposure
        cls.gfp_capture_channel.start()
        # block until stream notifier
        with tm.gst_bus_condition:
            result = tm.gst_bus_condition.wait(timeout=cls.BUS_TIMEOUT)
        # timeout handler
        if result:
            # enable the trigger pin for fluorescense
            cls.fluorescence.enable(True)
            time.sleep(exposure_time)
            img = cls.gfp_capture_channel.img_buffer.pop()
            cls._logger.debug("Sample acquired")
            cls.fluorescence.enable(False)
        else:
            cls._logger.warning("GFP stream timed out. Returning zeros matrix")
            img = np.zeros((1920, 2560, 1))
        cls.gfp_capture_channel.stop()
        return img

    @classmethod
    def exposure_stream_ctrl(cls, flag: bool) -> None:
        """
        Exposure stream controller

        :param flag: desired state
        :type flag: bool
        :raises GSTDeviceError: if GST device fails to initialize
        :raises LightingError: if the required lighting module is not initialized
        :raises ChannelError: if the required channel is not initialized
        """
        if not cls.tcam.initialized:
            raise GSTDeviceError
        if not cls.automatrix.initialized:
            raise LightingError
        if not cls.phase_stream_channel.initialized:
            raise ChannelError
        cls._logger.info("Setting Exposure stream to: %s", "ON" if flag else "OFF")
        if flag:
            # load the focus stream pattern into the automatrix
            cls.automatrix.load_pattern(cls.automatrix.focus.patterns[0])
            # enable the trigger pin outputting the pattern
            cls.automatrix.enable(True)
            cls.phase_stream_channel.start()
        else:
            cls.automatrix.enable(False)
            cls.phase_stream_channel.stop()

    @classmethod
    def focus_stream_ctrl(cls, flag: bool) -> None:
        """
        Focus stream controller

        :param flag: desired state
        :type flag: bool
        :raises GSTDeviceError: if GST device fails to initialize
        :raises LightingError: if the required lighting module is not initialized
        :raises ChannelError: if the required channel is not initialized
        """
        if not cls.tcam.initialized:
            raise GSTDeviceError
        if not cls.automatrix.initialized:
            raise LightingError
        if not cls.focus_stream_channel.initialized:
            raise ChannelError
        cls._logger.info("Setting Focus stream to: %s", "ON" if flag else "OFF")
        if flag:
            # load the focus stream pattern into the automatrix
            cls.automatrix.load_pattern(cls.automatrix.focus.patterns[0])
            # enable the trigger pin outputting the pattern
            cls.automatrix.enable(True)
            cls.focus_stream_channel.start()
        else:
            cls.automatrix.enable(False)
            cls.focus_stream_channel.stop()

    @classmethod
    def gfp_stream_ctrl(cls, flag: bool) -> None:
        """
        GFP stream controller

        :param flag: desired state
        :type flag: bool
        :raises GSTDeviceError: if GST device fails to initialize
        :raises LightingError: if the required lighting module is not initialized
        :raises ChannelError: if the required channel is not initialized
        """
        if not cls.tcam.initialized:
            raise GSTDeviceError
        if not cls.fluorescence.initialized:
            raise LightingError
        if not cls.gfp_stream_channel.initialized:
            raise ChannelError
        cls._logger.info("Setting GFP stream to: %s", "OFF" if flag else "ON")
        if flag:
            cls.fluorescence.enable(True)
            cls.gfp_stream_channel.start()
        else:
            cls.fluorescence.enable(False)
            cls.gfp_stream_channel.stop()
