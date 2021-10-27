# -*- coding: utf-8 -*-
"""
Temp Gauge
==========
Modified: 2021-06

Dependencies:
-------------
```
from typing import Tuple
from monitor.ui.dash.gauge import Gauge
from monitor.environment.state_manager import StateManager
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from typing import Optional, Tuple
from monitor.models.icb import ICB
from monitor.ui.components.gauge.gauge import Gauge
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import PropertyCondition, StateManager


class TempGauge(Gauge):
    def __init__(self, width: int, height: int):
        super().__init__(name='Temp.', width=width, height=height)
        with StateManager() as state:
            state.subscribe_property(
                _type=ICB,
                _property=PropertyCondition[ICB](
                    trigger=lambda old_icb, new_icb: old_icb.tp != new_icb.tp or old_icb.tm != new_icb.tm,
                    callback=self.reset_loaders,
                    callback_on_init=True
                )
            )
        events.temp_loader.register(self.set_load_state)

    async def reset_loaders(self, _: ICB) -> None:
        """
        Reset loading views if setpoint delta detected

        :param icb: imminent icb state 
        :type icb: ICB
        """
        self.load_state = False
        self.load_set = False

    def set_load_state(self, state: bool) -> None:
        """
        Set state of setpoint loading view

        :param state: if true the sensor mode has changed otherwise a setpoint change has occurred 
        :type state: bool
        """
        # state loading takes prescedence
        if state: self.load_state = True
        else: self.load_set = True

    def get_state(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        :return: gauge value and state descriptors 
        :rtype: Tuple[bool, str, str]
        """
        with StateManager() as state:
            icb = state.icb
        if not icb.initialized:
            return True, None, None
        # gauge disable guards
        if icb.tm < 2:  # first check if temp mode is not in controller state
            disabled = True
            value = 'OFF'
        elif icb.tc == -100:  # Now check for error state
            disabled = True
            value = 'ERR'
        else:  # nominal readinc
            disabled = False
            value = '{} °C'.format(icb.tc)
        current_set = str(icb.tp)
        return disabled, current_set, value
