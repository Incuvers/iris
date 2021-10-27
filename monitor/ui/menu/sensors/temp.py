# -*- coding: utf-8 -*-
"""
Temp Sensor Menu
================

Dependancies
------------
```
import logging
from monitor.models.icb import ICB
from monitor.ui.menu.sensors.menu import SensorMenu
from monitor.environment.state_manager import PropertyCondition, StateManager
from monitor.environment.thread_manager import ThreadManager as tma
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import logging
from monitor.models.icb import ICB
from monitor.ui.menu.sensors.menu import SensorMenu
from monitor.environment.state_manager import PropertyCondition, StateManager
from monitor.environment.thread_manager import ThreadManager as tma


class TempMenu(SensorMenu[float]):

    def __init__(self, main, surface):
        self._logger = logging.getLogger(__name__)
        super().__init__(main, surface, 'Temp',
                         ICB.TP_RANGE[0], ICB.TP_RANGE[1], ICB.TP_DEFAULT, '{:.1f} °C', 0.1, True)
        with StateManager() as state:
            state.subscribe_property(
                _type=ICB,
                _property=PropertyCondition[ICB](
                    trigger=lambda old_icb, new_icb: old_icb.tp != new_icb.tp or old_icb.tm != new_icb.tm,
                    callback=self.update,
                    callback_on_init=True
                )
            )
        self._logger.info("%s initialized", __name__)

    async def update(self, icb: ICB) -> None:
        """
        :param icb: [description]
        :type icb: ICB
        """
        # update current values
        self.value = icb.tp
        # do not override selector value if inactive
        if icb.tm == 2: self.selector.set_value(icb.tp)
        self.menu.set_title(self.get_title())
        self._logger.info("Updated setpoint: %s mode: %s", self.value, icb.tm)

    @tma.threaded(daemon=True)
    def set_temp(self, setpoint: float, mode: int) -> None:
        """
        Set temperature setpoint

        :param setpoint: temperature setpoint
        :type setpoint: float
        """
        with StateManager() as state:
            icb = state.icb
            icb.tm = mode
            icb.tp = setpoint
            state.commit(icb)

    def get_title(self) -> str:
        """
        Title constructor

        :return: sensor menu title
        :rtype: str
        """
        with StateManager() as state:
            icb = state.icb
        if not icb.initialized:
            title = "{}: -- %".format(self.name)
        elif icb.tm != 2:
            title = "{}: Off".format(self.name)
        else:
            title = "{}: {:.1f} °C".format(self.name, self.value)
        return title

    def cancel_value(self) -> None:
        """
        Resets candidate value
        """
        with StateManager() as state:
            icb = state.icb
        self.candidate_value = self.value
        if not icb.initialized:
            self.selector.set_value(self.min_val)
        if icb.tm == 2:
            self.selector.set_value(self.value)
        else:
            self.selector.set_value(self.min_val)
        self.menu.reset(1)

    def confirm_value(self) -> None:
        """
        Callback when user confirms the active value. The callback arguments are dependant on the modality.
        """
        # determine the sensor mode (if @ bounds mode is off)
        mode = 1 if self.candidate_value in [self.min_val, self.max_val] else 2
        self.set_temp(self.candidate_value, mode)
        self.menu.set_title(self.get_title())
        self.menu.reset(1)
