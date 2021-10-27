# -*- coding: utf-8 -*-
"""
Heater Sensor Menu
==================

Dependancies
------------
```
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


class HeaterMenu(SensorMenu[int]):

    def __init__(self, main, surface):
        self._logger = logging.getLogger(__name__)
        super().__init__(main, surface, 'Aux heater', 0, 100, ICB.HP_DEFAULT,
                         '{:d} %', 10, False)
        with StateManager() as state:
            state.subscribe_property(
                _type=ICB,
                _property=PropertyCondition[ICB](
                    trigger=lambda old_icb, new_icb: old_icb.hp != new_icb.hp,
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
        self.value = icb.hp
        self.selector.set_value(self.value)
        self.menu.set_title(self.get_title())
        self._logger.info("Updated setpoint: %s ", self.value)

    @tm.threaded(daemon=True)
    def set_heater_duty(self, duty: int) -> None:
        """
        Set auxilary heater duty cycle

        :param duty: heater duty setpoint
        :type duty: int
        """
        with StateManager() as state:
            icb = state.icb
            icb.hp = duty
            state.commit(icb)

    def get_title(self) -> str:
        """
        Title constructor

        :return: sensor menu title
        :rtype: str
        """
        return "{}: {:d} %".format(self.name, self.value)

    def cancel_value(self) -> None:
        """
        Resets candidate value
        """
        self.candidate_value = self.value
        self.selector.set_value(self.value)
        self.menu.reset(1)

    def confirm_value(self) -> None:
        """
        Callback when user confirms the active value. The callback arguments are dependant on the modality.
        """
        self.set_heater_duty(self.candidate_value)
        self.menu.set_title(self.get_title())
        self.menu.reset(1)
