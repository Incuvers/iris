# -*- coding: utf-8 -*-
"""
CO2 Sensor Menu
===============

Dependancies
------------
```
import logging
from monitor.models.icb import ICB
from monitor.ui.menu.sensors.menu import SensorMenu
from monitor.environment.state_manager import PropertyCondition, StateManager
from monitor.environment.thread_manager import ThreadManager as tm
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
from monitor.models.icb import ICB
from monitor.ui.menu.sensors.menu import SensorMenu
from monitor.environment.state_manager import PropertyCondition, StateManager
from monitor.environment.thread_manager import ThreadManager as tm


class CO2Menu(SensorMenu[float]):

    def __init__(self, main, surface):
        self._logger = logging.getLogger(__name__)
        super().__init__(main, surface, 'CO\u2082', ICB.CP_RANGE[0], ICB.CP_RANGE[1], ICB.CP_DEFAULT,
                         '{:.1f} %', 0.1, True)
        with StateManager() as state:
            state.subscribe_property(
                _type=ICB,
                _property=PropertyCondition[ICB](
                    trigger=lambda old_icb, new_icb: old_icb.cp != new_icb.cp or old_icb.cm != new_icb.cm,
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
        self.value = icb.cp
        # do not override selector value if inactive
        if icb.cm == 2: self.selector.set_value(icb.cp)
        else: self.selector.set_value(self.min_val)
        self.menu.set_title(self.get_title())
        self._logger.info("Updated setpoint: %s mode: %s", icb.cp, icb.cm)

    @tm.threaded(daemon=True)
    def set_co2(self, setpoint: float, mode: int) -> None:
        """
        Set co2 setpoint

        :param setpoint: co2 setpoint value
        :type setpoint: float
        """
        with StateManager() as state:
            icb = state.icb
            icb.cm = mode
            icb.cp = setpoint
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
        elif icb.cm != 2:
            title = "{}: Off".format(self.name)
        else:
            title = "{}: {:.1f} %".format(self.name, self.value)
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
        elif icb.cm == 2:
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
        self.set_co2(self.candidate_value, mode)
        self.menu.set_title(self.get_title())
        self.menu.reset(1)
