# -*- coding: utf-8 -*-
"""
Imaging Profile
===============
Modified: 2021-11

Model object for imaging profile info

Dependencies:
-------------
```
from typing import Any, Dict
import monitor.imaging.constants as IC
from monitor.logs.formatter import pformat
from monitor.models.state import StateModel
```

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from typing import Any, Dict
import monitor.imaging.constants as IC
from monitor.logs.formatter import pformat
from monitor.models.state import StateModel


class ImagingProfile(StateModel):

    FILENAME = 'imaging.json'

    def __init__(self):
        super().__init__(
            _id=-1,
            filename = self.FILENAME
        )
        # set defaults
        self.id = -1
        self.name = "Default Imaging Profile"
        self.dpc_inner_radius = 3.0
        self.dpc_outer_radius = 4.0
        self.dpc_brightness = 0
        self.dpc_gain = 0
        self.dpc_exposure = 0
        self.gfp_brightness = 0
        self.gfp_gain = 0
        self.gfp_exposure = 0
        self.gfp_capture = False

    def __repr__(self) -> str:
        return "ImagingProfile: {}".format(pformat(self.serialize()))

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize object into json compatible dict

        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        return {
            'id': self.id,
            'name': self.name,
            'dpc_brightness': self.dpc_brightness,
            'gfp_brightness': self.gfp_brightness,
            'dpc_gain': self.dpc_gain,
            'gfp_gain': self.gfp_gain,
            'dpc_exposure': self.dpc_exposure,
            'gfp_exposure': self.gfp_exposure,
            'dpc_inner_radius': self.dpc_inner_radius,
            'dpc_outer_radius': self.dpc_outer_radius,
            'gain_min': self.gain_min,
            'gain_max': self.gain_max,
            'brightness_min': self.brightness_min,
            'brightness_max': self.brightness_max,
            'dpc_exposure_min': self.dpc_exposure_min,
            'dpc_exposure_max': self.dpc_exposure_max,
            'gfp_exposure_min': self.gfp_exposure_min,
            'gfp_exposure_max': self.gfp_exposure_max,
            'gfp_capture': self.gfp_capture
        }

    def deserialize(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            # guard on attribute set on read only properties
            if k not in ['gain_min', 'gain_max', 'brightness_max', 'brightness_min', 'gfp_exposure_min',
                         'gfp_exposure_max', 'dpc_exposure_max', 'dpc_exposure_min']:
                setattr(self, k, v)

    @property
    def name(self) -> str:
        """
        Get imaging profile name

        :return: imaging profile name
        :rtype: str
        """
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set imaging profile name

        :param name: imaging profile name
        :type name: str
        """
        self.__name = name

    @property
    def dpc_brightness(self) -> int:
        """
        Get dpc channel brightness (tcam-src units)

        :return: dpc imaging brightness in tcam-src units
        :rtype: int
        """
        return self.__dpc_brightness

    @dpc_brightness.setter
    def dpc_brightness(self, dpc_brightness: int) -> None:
        """
        Set dpc channel brightness (tcam-src units)

        :param dpc_brightness: dpc imaging brightness in tcam-src units
        :type dpc_brightness: int
        """
        self.__dpc_brightness = dpc_brightness

    @property
    def dpc_gain(self) -> int:
        """
        Get dpc channel gain (tcam-src units)

        :return: dpc imaging gain in tcam-src units
        :rtype: int
        """
        return self.__dpc_gain

    @dpc_gain.setter
    def dpc_gain(self, dpc_gain: int) -> None:
        """
        Set dpc channel gain (tcam-src units)

        :param dpc_gain: dpc imaging gain in tcam-src units
        :type dpc_gain: int
        """
        self.__dpc_gain = dpc_gain

    @property
    def dpc_exposure(self) -> int:
        """
        Get dpc channel exposure (μs)

        :return: dpc channel exposure in μs
        :rtype: int
        """
        return self.__dpc_exposure

    @dpc_exposure.setter
    def dpc_exposure(self, dpc_exposure: int) -> None:
        """
        Set dpc channel exposure (μs)

        :param dpc_exposure: dpc channel exposure in μs
        :type dpc_exposure: int
        """
        self.__dpc_exposure = dpc_exposure

    @property
    def dpc_inner_radius(self) -> float:
        """
        Get automatrix inner radius (units?)

        :return: automatrix inner radius
        :rtype: float
        """
        return self.__dpc_inner_radius

    @dpc_inner_radius.setter
    def dpc_inner_radius(self, dpc_inner_radius: float) -> None:
        """
        Set automatrix inner radius (units?)

        :param dpc_inner_radius: automatrix inner radius
        :type dpc_inner_radius: float
        """
        self.__dpc_inner_radius = dpc_inner_radius

    @property
    def dpc_outer_radius(self) -> float:
        """
        Get automatrix outer radius (units?)

        :return: automatrix outer radius
        :rtype: float
        """
        return self.__dpc_outer_radius

    @dpc_outer_radius.setter
    def dpc_outer_radius(self, dpc_outer_radius: float) -> None:
        """
        Set automatrix outer radius (units?)

        :param dpc_outer_radius: automatrix outer radius
        :type dpc_outer_radius: float
        """
        self.__dpc_outer_radius = dpc_outer_radius

    @property
    def gfp_capture(self) -> bool:
        """
        Get gfp channel enable state

        :return: gfp channel state enable flag
        :rtype: bool
        """
        return self.__gfp_capture

    @gfp_capture.setter
    def gfp_capture(self, state: bool) -> None:
        """
        Set gfp channel enable state

        :param state: gfp channel enable state
        :type state: bool
        """
        self.__gfp_capture = state

    @property
    def gfp_brightness(self) -> int:
        """
        Get gfp channel brightness (tcam-src units)

        :return: gfp channel brightness in tcam-src units
        :rtype: int
        """
        return self.__gfp_brightness

    @gfp_brightness.setter
    def gfp_brightness(self, gfp_brightness: int) -> None:
        """
        Set gfp channel brightness (tcam-src units)

        :param gfp_brightness: gfp channel brightness
        :type gfp_brightness: int
        """
        self.__gfp_brightness = gfp_brightness

    @property
    def gfp_gain(self) -> int:
        """
        Get gfp channel gain (tcam-src units)

        :return: gfp channel gain in tcam-src units
        :rtype: int
        """
        return self.__gfp_gain

    @gfp_gain.setter
    def gfp_gain(self, gfp_gain: int) -> None:
        """
        Set gfp channel gain (tcam-src units)

        :param gfp_gain: gfp channel gain in tcam-src units
        :type gfp_gain: int
        """
        self.__gfp_gain = gfp_gain

    @property
    def gfp_exposure(self) -> int:
        """
        Get gfp channel exposure (μs)

        :return: gfp channel exposure in μs
        :rtype: int
        """
        return self.__gfp_exposure

    @gfp_exposure.setter
    def gfp_exposure(self, gfp_exposure: int) -> None:
        """
        Set gfp channel exposure (μs)

        :param gfp_exposure: gfp channel exposure in μs
        :type gfp_exposure: int
        """
        self.__gfp_exposure = gfp_exposure

    @property
    def gain_min(self) -> int:
        """
        Get tcam minimum gain (tcam-src units)

        :return: tcam minimum gain in tcam-src units
        :rtype: int
        """
        return 4

    @property
    def gain_max(self) -> int:
        """
        Get tcam maximum gain (tcam-src units)

        :return: tcam maximum gain in tcam-src units
        :rtype: int
        """
        return 63

    @property
    def brightness_min(self) -> int:
        """
        Get tcam minimum brightness (tcam-src units)

        :return: tcam minimum brightness in tcam-src units
        :rtype: int
        """
        return 0

    @property
    def brightness_max(self) -> int:
        """
        Get tcam maximum brightness (tcam-src units)

        :return: tcam maximum brightness in tcam-src units
        :rtype: int
        """
        return 4096

    @property
    def dpc_exposure_max(self) -> int:
        """
        Get maximum dpc channel exposure  (μs)

        :return: maximum dpc channel exposure in μs
        :rtype: int
        """
        return IC.dpc_grade_to_exposure(grade=100)

    @property
    def gfp_exposure_max(self) -> int:
        """
        Get maximum gfp channel exposure (μs)

        :return: maximum gfp channel exposure in μs 
        :rtype: int
        """
        return IC.gfp_grade_to_exposure(grade=100)

    @property
    def dpc_exposure_min(self) -> int:
        """
        Get minimum dpc channel exposure (μs)

        :return: minimum dpc channel exposure in μs
        :rtype: int
        """
        return IC.dpc_grade_to_exposure(grade=0)

    @property
    def gfp_exposure_min(self) -> int:
        """
        Get minimum gfp channel exposure value (μs)

        :return: minimum gfp channel exposure value in μs
        :rtype: int
        """
        return IC.gfp_grade_to_exposure(grade=0)
