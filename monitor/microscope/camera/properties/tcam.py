#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GST Properties
==============
Modified: 2021-01

Dependencies:
-------------
```
import logging.config
from pprint import pformat
from monitor.environment.context_manager import ContextManager
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import gi  # type: ignore
import logging
from collections import OrderedDict

from pprint import pformat
from typing import Any, Dict, List, Tuple

import monitor.imaging.constants as ic
from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.state_manager import StateManager
from monitor.environment.context_manager import ContextManager
from monitor.microscope.camera.properties.resolution import CMOSConfig
from monitor.exceptions.microscope import GSTDeviceError, NoGSTDeviceError, MultipleGSTDevicesError, PropertyError
# HACK: to fix lint E402
try:
    gi.require_version("Gst", "1.0")
finally:
    from gi.repository import Gst  # type: ignore


class TcamProperties:
    """
    caps = {
        video/x-raw: {
            GRAY8: {
                (3872,2764): ['6/1', '5/1', '4/1', '3/1', '2/1'],
                (3664,2748): ['7/1', '6/1', '5/1', '4/1', '3/1', '2/1'],
                ...
            }
            GRAY16_LE: {
                (3872,2764): ['6/1', '5/1', '4/1', '3/1', '2/1'],
                (3664,2748): ['7/1', '6/1', '5/1', '4/1', '3/1', '2/1'],
                ...
            }
        }
    }
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self.initialized = False
        with ContextManager() as context:
            self.video = context.get_env('TCAM_VIDEO_FORMAT', "video/x-raw")
            self.fmt = context.get_env('TCAM_PIXEL_FORMAT', "GRAY8")
        with StateManager() as state:
            state.subscribe_isv(ImagingProfile, self.validator)
        self._logger.info("%s instantiated successfully", __name__)

    def __repr__(self) -> str:
        return "Tcam Profile: {}".format(pformat(self.getattrs()))

    def getattrs(self) -> Dict[str, Any]:
        """
        Iteratively get all object properties and values

        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        attributes: Dict[str, Any] = {}
        for k, v in vars(self).items():
            if k not in ['_logger', 'video', 'fmt']:
                attributes[k.split('__')[-1]] = v
        return attributes

    def setattrs(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    def probe(self) -> Tuple[CMOSConfig, CMOSConfig]:
        """
        Probe tcam hardware and populate cmos resolution properties

        :raises PropertyError: if the tcam property probe does not contain the expected value
        :return: ultra and medium resolutions for use in channel init
        :rtype: Tuple[CMOSConfig, CMOSConfig]
        """
        self.model, self.serial, self.identifier, self.backend, tcam_properties, caps = self.get_hardware_properties()
        try:
            exposure: Dict[str, int] = tcam_properties['Exposure Time (us)']
            self.exposure_range = (exposure['min'], exposure['max'])
            gain: Dict[str, int] = tcam_properties['Gain']
            self.gain_range = (gain['min'], gain['max'])
            brightness: Dict[str, int] = tcam_properties['Brightness']
            self.brightness_range = (brightness['min'], brightness['max'])
        except KeyError as exc:
            self._logger.critical("Expected tcam property key not found: %s", exc)
            raise PropertyError from exc
        # resolutions are populated by ordered dictionary which translate to a sequential decrease
        # in resolution as we traverse down the keys. The indices are based on the known location of
        # the desired resolutions
        res_keys: List[Tuple[int, int]] = list(caps[self.video][self.fmt].keys())
        # setting all resolutions to their maximum allotted framerate [0]
        self.max = CMOSConfig(
            name='max', resolution=res_keys[0], framerate=caps[self.video][self.fmt][res_keys[0]][0])
        self.ultra = CMOSConfig(
            name='ultra', resolution=res_keys[1], framerate=caps[self.video][self.fmt][res_keys[1]][0])
        self.high = CMOSConfig(
            name='high', resolution=res_keys[3], framerate=caps[self.video][self.fmt][res_keys[3]][0])
        self.med = CMOSConfig(
            name='med', resolution=res_keys[4], framerate=caps[self.video][self.fmt][res_keys[4]][0])
        self.low = CMOSConfig(
            name='low', resolution=res_keys[6], framerate=caps[self.video][self.fmt][res_keys[6]][0])
        self.initialized = True
        return self.med, self.ultra

    def validator(self, imaging_profile: ImagingProfile) -> bool:
        """
        Validate updated imaging profile tcam properties are within the allowed ranges

        :param imaging_profile: [description]
        :type imaging_profile: ImagingProfile
        :return: [description]
        :rtype: bool
        """
        # perform checks on values against tcam properties
        gain_min, gain_max = self.gain_range
        exposure_min, exposure_max = self.exposure_range
        brightness_min, brightness_max = self.brightness_range
        # dpc gain check
        if gain_min > imaging_profile.dpc_gain < gain_max:
            return False
        # gfp gain check
        if gain_min > imaging_profile.gfp_gain < gain_max:
            return False
        # dpc exposure check
        if exposure_min > imaging_profile.dpc_exposure < exposure_max:
            return False
        # gfp exposure check
        if exposure_min > imaging_profile.gfp_exposure < exposure_max:
            return False
        # dpc brightness check
        if brightness_min > imaging_profile.dpc_brightness < brightness_max:
            return False
        # gfp brightness check
        if brightness_min > imaging_profile.gfp_brightness < brightness_max:
            return False
        return True

    @property
    def initialized(self) -> bool:
        return self.__initialized

    @initialized.setter
    def initialized(self, status: bool) -> None:
        self.__initialized = status

    @property
    def model(self) -> str:
        return self.__model

    @model.setter
    def model(self, model: str) -> None:
        self.__model = model

    @property
    def serial(self) -> str:
        return self.__serial

    @serial.setter
    def serial(self, serial: str) -> None:
        self.__serial = serial

    @property
    def identifier(self) -> str:
        return self.__identifier

    @identifier.setter
    def identifier(self, identifier: str) -> None:
        self.__identifier = identifier

    @property
    def backend(self) -> str:
        return self.__backend

    @backend.setter
    def backend(self, backend: str) -> None:
        self.__backend = backend

    @property
    def dpc_light_exposure(self) -> float:
        return 0.25

    @property
    def gfp_light_exposure(self) -> float:
        return ic.gfp_grade_to_exposure(grade=100) // 1000000

    @property
    def scan_modes(self) -> List[int]:
        return [0, 1, 2, 3, 4]

    @property
    def exposure_range(self) -> Tuple[int, int]:
        return self.__exposure_range

    @exposure_range.setter
    def exposure_range(self, range: Tuple[int, int]) -> None:
        self.__exposure_range = range

    @property
    def brightness_range(self) -> Tuple[int, int]:
        return self.__brightness_range

    @brightness_range.setter
    def brightness_range(self, range: Tuple[int, int]) -> None:
        self.__brightness_range = range

    @property
    def gain_range(self) -> Tuple[int, int]:
        return self.__gain_range

    @gain_range.setter
    def gain_range(self, range: Tuple[int, int]) -> None:
        self.__gain_range = range

    @property
    def max(self) -> CMOSConfig:
        return self.__max

    @max.setter
    def max(self, cmos_config: CMOSConfig) -> None:
        self.__max = cmos_config

    @property
    def ultra(self) -> CMOSConfig:
        return self.__ultra

    @ultra.setter
    def ultra(self, cmos_config: CMOSConfig) -> None:
        self.__ultra = cmos_config

    @property
    def high(self) -> CMOSConfig:
        return self.__high

    @high.setter
    def high(self, cmos_config: CMOSConfig) -> None:
        self.__high = cmos_config

    @property
    def medium(self) -> CMOSConfig:
        return self.__medium

    @medium.setter
    def medium(self, cmos_config: CMOSConfig) -> None:
        self.__medium = cmos_config

    @property
    def low(self) -> CMOSConfig:
        return self.__low

    @low.setter
    def low(self, cmos_config: CMOSConfig) -> None:
        self.__low = cmos_config

    # TODO: deprecate dict and tuple formatting and return a dict to pass into setattr()
    @staticmethod
    def get_hardware_properties() -> Tuple[str, str, str, str, Dict[str, Dict[str, int]],
                                           Dict[str, Dict[str, Dict[Tuple[int, int], List[str]]]]]:
        """
        Creates temporary gst source element to fetch the serial properties
        """
        if not Gst.init_check(''):
            # here we failed to init GST
            raise GSTDeviceError
        source = Gst.ElementFactory.make("tcamsrc")
        serials = source.get_device_serials()
        # if no device serials detected raise IOError
        if len(serials) == 0:
            raise NoGSTDeviceError
        if len(serials) > 1:
            raise MultipleGSTDevicesError
        serial: str = serials[-1]
        # PEP-0526 type annotation first
        return_value: bool
        model: str
        identifier: str
        backend: str
        return_value, model, identifier, backend = source.get_device_info(serial)
        # return value would be False when a non-existant serial is used
        if not return_value:
            raise PropertyError
        # setup READY state pipeline
        source.set_property("serial", serial)
        # probe & filter tcam property fields
        tcam_properties: Dict[str, Dict[str, int]] = {
            'Brightness': {}, 'Gain': {}, 'Exposure Time (us)': {}}
        property_names = source.get_tcam_property_names()
        for name in property_names:
            (ret, value, min_value, max_value, _, _, _, _, _, _) = source.get_tcam_property(name)
            if (not ret) or (name not in ('Brightness', 'Gain', 'Exposure Time (us)')): continue
            tcam_properties[name]['min'] = min_value
            tcam_properties[name]['max'] = max_value
            tcam_properties[name]['value'] = value
        source.set_state(Gst.State.READY)
        try:
            tcam_caps: Dict[str, Dict[str, Dict[Tuple[int, int], List[str]]]] = OrderedDict()
            caps = source.get_static_pad("src").query_caps()
            for x in range(caps.get_size()):
                try:
                    structure = caps.get_structure(x)
                    name = structure.get_name()
                    fmt = structure.get_value("format")
                    width = structure.get_value("width")
                    height = structure.get_value("height")
                    resolution = (width, height)
                    framerates = structure.get_value("framerate")
                    rates = list()
                    if isinstance(framerates, Gst.ValueList):
                        for y in range(Gst.ValueList.get_size(framerates)):
                            rates.append(str(Gst.ValueList.get_value(framerates, y)))
                    if name not in tcam_caps:
                        tcam_caps[name] = {}
                    if fmt not in tcam_caps[name]:
                        tcam_caps[name][fmt] = {}
                    tcam_caps[name][fmt][resolution] = rates
                except TypeError as exc:
                    raise PropertyError from exc
        finally:
            # set probing pipeline to null
            source.set_state(Gst.State.NULL)
        return (model, serial, identifier, backend, tcam_properties, tcam_caps)
