# -*- coding: utf-8 -*-
"""
RH Gauge
========
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
from monitor.ui.components.gauge.gauge import Gauge
from monitor.environment.state_manager import StateManager


class RHGauge(Gauge):
    def __init__(self, width: int, height: int):
        super().__init__(name='RH', width=width, height=height)

    def get_state(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        :return: gauge value and state descriptors 
        :rtype: Tuple[bool, str, str]
        """
        with StateManager() as state:
            icb = state.icb
        if not icb.initialized:
            return True, None, None
        # Check for error state
        if icb.rh == -100:
            disabled = True
            value = 'ERR'
        else:  # nominal reading
            value = '-- %'
            disabled = True
            # self.value = '{} %'.format(value)
        current_set = '--'
        return disabled, current_set, value
