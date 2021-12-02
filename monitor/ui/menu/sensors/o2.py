# -*- coding: utf-8 -*-
"""
O2 Sensor Menu
==============

Dependancies
------------
```
from .incuvers_settings_ui import IncuversSettingsUI
from .pygameMenu import Menu
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import logging
from typing import Callable
from monitor.models.icb import ICB
from monitor.ui.menu.sensors.menu import SensorMenu
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager as tm


def o2_setpoint_delta(func: Callable) -> Callable:
    async def wrapper(self, sensorframe: ICB):
        if sensorframe.op != self.op or sensorframe.om != self.om:
            await func(self, sensorframe)
    return wrapper


class O2Menu(SensorMenu[float]):

    # cached current values
    op = 0
    om = 0

    def __init__(self, main, surface):
        self._logger = logging.getLogger(__name__)
        super().__init__(main, surface, 'O\u2082', ICB.OP_RANGE[0], ICB.OP_RANGE[1], ICB.OP_DEFAULT,
                         '{:.1f} %', 0.1, True)
        with StateManager() as state:
            state.subscribe(ICB, self.update)
        self._logger.info("%s initialized", __name__)

    @o2_setpoint_delta
    async def update(self, icb: ICB) -> None:
        """
        :param icb: [description]
        :type icb: ICB
        """
        # update current values
        self.op = icb.op
        self.om = icb.om
        self.value = icb.op
        # do not override selector value if inactive
        if self.om == 2: self.selector.set_value(icb.op)
        self.menu.set_title(self.get_title())
        self._logger.info("Updated setpoint: %s mode: %s", self.op, self.om)

    @tm.threaded(daemon=True)
    def set_o2(self, setpoint: float, mode: int) -> None:
        """
        Set o2 setpoint

        :param setpoint: o2 setpoint value
        :type setpoint: float
        """
        with StateManager() as state:
            icb = state.icb
            icb.om = mode
            icb.op = setpoint
            state.commit(icb)

    def get_title(self) -> str:
        """
        Title constructor

        :return: sensor menu title
        :rtype: str
        """
        if self.om != 2: title = "{}: Off".format(self.name)
        else: title = "{}: {:.1f} %".format(self.name, self.value)
        return title

    def cancel_value(self) -> None:
        """
        Resets candidate value
        """
        self.candidate_value = self.op
        if self.om == 2: self.selector.set_value(self.op)
        else: self.selector.set_value(self.min_val)
        self.menu.reset(1)

    def confirm_value(self) -> None:
        """
        Callback when user confirms the active value. The callback arguments are dependant on the modality.
        """
        # determine the sensor mode (if @ bounds mode is off)
        mode = 1 if self.candidate_value in [self.min_val, self.max_val] else 2
        self.set_o2(self.candidate_value, mode)
        self.menu.set_title(self.get_title())
        self.menu.reset(1)
