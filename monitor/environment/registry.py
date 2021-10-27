# -*- coding: utf-8 -*-
"""
State Manager
=============
Modified: 2021-05

Stores state variable subscribers and independant system validators.

Dependancies
------------
```
from typing import Awaitable, Callable, List

from monitor.models.icb import ICB
from monitor.models.device import Device
from monitor.models.protocol import Protocol
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
from typing import Any, Callable, Coroutine, Dict, List, Tuple

from monitor.models.icb import ICB
from monitor.models.device import Device
from monitor.models.protocol import Protocol
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile


class CallbackRegistry:
    # validator registries
    # these are single functions but in order for them to be modified they must be encapsulated in an object
    icb_isv: List[Callable[[ICB], bool]] = []
    ip_isv: List[Callable[[ImagingProfile], bool]] = []
    # subscriber registries
    icb: List[Callable[[ICB], Coroutine[Any, Any, None]]] = []
    device: List[Callable[[Device], Coroutine[Any, Any, None]]] = []
    experiment: List[Callable[[Experiment], Coroutine[Any, Any, None]]] = []
    protocol: List[Callable[[Protocol], Coroutine[Any, Any, None]]] = []
    ip: List[Callable[[ImagingProfile], Coroutine[Any, Any, None]]] = []
    ip_properties: Dict[Callable[[ImagingProfile], Coroutine[Any, Any, None]],
                        List[Tuple[Callable[[ImagingProfile, ImagingProfile], bool], bool]]] = {}
    experiment_properties: Dict[Callable[[Experiment], Coroutine[Any, Any, None]],
                                List[Tuple[Callable[[Experiment, Experiment], bool], bool]]] = {}
    protocol_properties: Dict[Callable[[Protocol], Coroutine[Any, Any, None]],
                              List[Tuple[Callable[[Protocol, Protocol], bool], bool]]] = {}
    icb_properties: Dict[Callable[[ICB], Coroutine[Any, Any, None]],
                         List[Tuple[Callable[[ICB, ICB], bool], bool]]] = {}
    device_properties: Dict[Callable[[Device], Coroutine[Any, Any, None]],
                            List[Tuple[Callable[[Device, Device], bool], bool]]] = {}


class StateRegistry:
    # state variables
    icb: ICB = ICB()
    protocol: Protocol = Protocol()
    device: Device = Device()
    imaging_profile: ImagingProfile = ImagingProfile()
    experiment: Experiment = Experiment()
