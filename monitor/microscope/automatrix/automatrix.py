#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automatrix
==========
Modified: 2020-09

Dependencies:
-------------
```
import logging.config
import numpy as np
import wiringpi
from monitor.imaging.microscope.automatrix.stream import AutomatrixStream
from monitor.imaging.microscope.automatrix.hardware import AutomatrixHardware
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import time
import logging
import wiringpi  # type: ignore
import numpy as np
from typing import List

from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.state_manager import PropertyCondition, StateManager
from monitor.microscope.automatrix.stream import AutomatrixStream
from monitor.microscope.automatrix.hardware import AutomatrixHardware


class Automatrix:

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.outer_radius_set = False
        self.inner_radius_set = False
        self.dpc_set = False
        self.focus_set = False
        self.dpc = AutomatrixStream()
        self.focus = AutomatrixStream()
        # counter for elapsed time the automatrix is active
        self.elapsed_active = 0
        with StateManager() as state:
            state.subscribe_property(
                _type=ImagingProfile,
                _property=PropertyCondition[ImagingProfile](
                    trigger=lambda old_ip, new_ip:
                        old_ip.dpc_inner_radius != new_ip.dpc_inner_radius or
                        old_ip.dpc_outer_radius != new_ip.dpc_outer_radius,
                    callback=self.set_radius,
                    callback_on_init=True
                )
            )
            # set dpc inner and outerr radius here
            imaging_profile = state.imaging_profile
            self.inner_radius = imaging_profile.dpc_inner_radius
            self.outer_radius = imaging_profile.dpc_outer_radius
            self._logger.info("Updated automatrix inner radius: %s and outer radius: %s.",
                self.inner_radius, self.outer_radius)
            self.configure()
        self._logger.info("Instantiation successful.")

    def __del__(self):
        """
        Deactivate and shift in low bits before dereferencing automatrix
        """
        # self.load_pattern(pattern=[0] * 32)  # equivalent to SRCLR

    @property
    def initialized(self) -> bool:
        """
        Get automatrix init status

        :return: automatrix init status
        :rtype: bool
        """
        return all(
            [
                self.outer_radius_set,
                self.inner_radius_set,
                self.dpc_set,
                self.focus_set,
            ]
        )

    @property
    def outer_radius(self) -> float:
        return self.__outer_radius

    @outer_radius.setter
    def outer_radius(self, radius: float) -> None:
        self.__outer_radius = radius
        self.outer_radius_set = True

    @property
    def inner_radius(self) -> float:
        return self.__inner_radius

    @inner_radius.setter
    def inner_radius(self, radius: float) -> None:
        self.__inner_radius = radius
        self.inner_radius_set = True

    @property
    def dpc(self) -> AutomatrixStream:
        return self.__dpc

    @dpc.setter
    def dpc(self, stream: AutomatrixStream) -> None:
        self.__dpc = stream
        self.dpc_set = True

    @property
    def focus(self) -> AutomatrixStream:
        return self.__focus

    @focus.setter
    def focus(self, stream: AutomatrixStream) -> None:
        self.__focus = stream
        self.focus_set = True

    def initialize_hardware(self):
        # setup wiringPi SPI
        wiringpi.wiringPiSetupGpio()
        wiringpi.pinMode(AutomatrixHardware.TRIGGER, wiringpi.OUTPUT)
        wiringpi.wiringPiSPISetup(AutomatrixHardware.SPI_CHANNEL, AutomatrixHardware.SPI_SPEED)

    async def set_radius(self, imaging_profile: ImagingProfile) -> None:
        """
        Set the radius for the automatrix lighting. This method is called every time the imaging
        """
        self.outer_radius = imaging_profile.dpc_outer_radius
        self.inner_radius = imaging_profile.dpc_inner_radius
        self._logger.info("Updated automatrix inner radius: %s and outer radius: %s.\
            Reconfiguring automatrix patterns.", self.inner_radius, self.outer_radius)
        self.configure()

    def configure(self):
        # clear previous patterns
        self.focus.clear()
        self.dpc.clear()
        self.enable(False)
        # compute focus patterns
        focus_pattern = self._generate_focus_pattern(self.outer_radius, self.inner_radius)
        # Add the focus pattern to the stream map
        self.focus.set_pattern(focus_pattern)
        # compute focus patterns
        dpc_patterns = self._generate_dpc_patterns(self.outer_radius, self.inner_radius)
        # create and configure new automatrix stream
        for pattern in dpc_patterns:
            pattern_print = pattern.astype(np.uint8)
            self._logger.debug("Added new dpc pattern: \n%s", pattern_print)
            self.dpc.set_pattern(pattern)
        # Add the dpc patterns to the stream map
        self._logger.debug("Config successful.")

    def load_pattern(self, pattern: List[int]):
        """
        Load the specified automatrix stream data through the spi interface.
        """
        wiringpi.wiringPiSPIDataRW(AutomatrixHardware.SPI_CHANNEL, bytes(pattern.copy()))
        self._logger.debug("Pattern loaded: %s", bytes(pattern))

    def enable(self, active: bool):
        """
        Write high or low to the automatrix trigger pin

        :param active: True is activate; False is deactivate
        """
        if active:
            wiringpi.digitalWrite(AutomatrixHardware.TRIGGER, AutomatrixHardware.ACTIVE_HIGH)
            self.elapsed_active = time.time()
        else:
            wiringpi.digitalWrite(AutomatrixHardware.TRIGGER, not AutomatrixHardware.ACTIVE_HIGH)
            if self.elapsed_active != 0:
                delta = round(time.time() - self.elapsed_active, 2)
                self.elapsed_active = 0
                self._logger.info("Elapsed time active: %ss", delta)
        self._logger.debug("Automatrix enable: %s", active)

    @staticmethod
    def _generate_dpc_patterns(outer_radius: float, inner_radius: float) -> List[np.ndarray]:
        """
        Computes the DPC LED patterns based on the selected dialation sizes. This results in
        four half circle patterns corresponding to the cardinal directions in sequence: upper, lower,
        left, right.
        """
        # tweak to center the circle
        ox, oy = AutomatrixHardware.MATRIX_DIM / 2 - 0.5, AutomatrixHardware.MATRIX_DIM / 2 - 0.5
        or_sq, ir_sq = outer_radius**2, inner_radius**2
        shape = (AutomatrixHardware.MATRIX_DIM, AutomatrixHardware.MATRIX_DIM)
        upper_px = np.zeros(shape, dtype=np.bool_)
        lower_px = np.zeros(shape, dtype=np.bool_)
        left_px = np.zeros(shape, dtype=np.bool_)
        right_px = np.zeros(shape, dtype=np.bool_)
        for i in np.arange(AutomatrixHardware.MATRIX_DIM):
            for j in np.arange(AutomatrixHardware.MATRIX_DIM):
                if not ((i - ox)**2 + (j - oy)**2 > or_sq):
                    if ((i - ox)**2 + (j - oy)**2 > ir_sq):
                        if i > ox:
                            left_px[i, j] = 1
                        if i < ox:
                            right_px[i, j] = 1
                        if j > oy:
                            upper_px[i, j] = 1
                        if j < oy:
                            lower_px[i, j] = 1
        return [upper_px, lower_px, left_px, right_px]

    @staticmethod
    def _generate_focus_pattern(outer_radius: float, inner_radius: float) -> np.ndarray:
        """
        Computes one DPC LED pattern based on the selected dialation sizes. This results in one half
        circle pattern of arbitrary direction.
        """
        left_px = np.zeros((AutomatrixHardware.MATRIX_DIM,
                           AutomatrixHardware.MATRIX_DIM), dtype=np.bool_)
        ox, oy = AutomatrixHardware.MATRIX_DIM / 2 - \
            0.5, AutomatrixHardware.MATRIX_DIM / 2 - 0.5   # tweak to center the circle
        or_sq, ir_sq = outer_radius**2, inner_radius**2
        for i in np.arange(AutomatrixHardware.MATRIX_DIM):
            for j in np.arange(AutomatrixHardware.MATRIX_DIM):
                rad_sqr_ij = (i - ox)**2 + (j - oy)**2
                if ir_sq < rad_sqr_ij < or_sq:
                    if i > ox:
                        left_px[i, j] = 1
        return left_px
