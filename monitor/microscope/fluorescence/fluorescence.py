#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fluorescence
============
Modified: 2021-01

Fluorescense interface with watchdog integration.

Dependencies:
-------------
```
import logging.config
import wiringpi
from monitor.microscope.fluorescence.hardware import FluorescenceHardware
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import time
import wiringpi  # type:ignore
import logging

from monitor.environment.thread_manager import ThreadManager as tm
from monitor.microscope.fluorescence.hardware import FluorescenceHardware


class Fluorescence:

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.initialized = False
        self.state = False
        # counter for elapsed time the automatrix is active
        self.elapsed_active = 0
        self.cooldown = False
        self._logger.info("Initialized fluorescence trigger pin to status: %s", self.state)
        self._logger.info("Instantiation successful.")

    @property
    def initialized(self) -> bool:
        return self.__initialized

    @initialized.setter
    def initialized(self, status: bool) -> None:
        self.__initialized = status

    def initialize_hardware(self):
        wiringpi.wiringPiSetupGpio()
        wiringpi.pinMode(FluorescenceHardware.TRIGGER, wiringpi.OUTPUT)
        self.initialized = True

    @tm.threaded(daemon=True)
    def watchdog_timer(self) -> None:
        """
        Internal counter to circumvent LED overhead. This timer unconditionally cascades into the
        cooldown timer.
        """
        self._logger.info("Entering watchdog phase")
        wd_timer = 0
        while True:
            # exit watchdog and enter cd if fluo led is off
            if not self.state:
                self._logger.info("Returned early from watchdog phase")
                return
            if wd_timer >= FluorescenceHardware.GFP_BURNOUT:
                self.enable(False)
                self._logger.warning("Fluorescence watchdog kicked due to overheating.")
                break
            time.sleep(1)
            wd_timer += 1
        self.cooldown = True
        self._logger.info("Exiting watchdog phase")
        self.cooldown_timer()

    def cooldown_timer(self) -> None:
        """
        Cooldown timer
        """
        self._logger.info("Entering cooldown phase")
        cd_timer = 0
        while True:
            if cd_timer >= FluorescenceHardware.GFP_COOLDOWN:
                break
            time.sleep(1)
            cd_timer += 1
        self.cooldown = False
        self._logger.info("Exiting cooldown phase")

    def enable(self, active: bool) -> None:
        """
        Write high or low to the fluorescence trigger pin

        :param active: True is activate; False is deactivate
        """
        # Do not activate if we are in cooldown phase
        if active and not self.cooldown:
            wiringpi.digitalWrite(
                FluorescenceHardware.TRIGGER,
                FluorescenceHardware.ACTIVE_HIGH
            )
            self.state = True
            # start watchdog
            self.watchdog_timer()
            self.elapsed_active = time.time()
        else:
            wiringpi.digitalWrite(
                FluorescenceHardware.TRIGGER,
                not FluorescenceHardware.ACTIVE_HIGH
            )
            self.state = False
            if self.elapsed_active != 0:
                delta = round(time.time() - self.elapsed_active, 2)
                self.elapsed_active = 0
                self._logger.info("Elapsed time active: %ss", delta)
        self._logger.info("Fluorescence trigger pin to status: %s", self.state)
