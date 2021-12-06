#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Event Types
===========
Modified: 2021-04

Namespace to store the system event types

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import numpy as np
from typing import Any, Callable, Dict, Union
from monitor.events.event import Event
from monitor.events.pipeline import Pipeline


class Registry:
    """
    Interpreting Typing schema:
    Callable[[argtype], rtype]
    """
    # events
    system_status = Event[Callable[[str, str], None]]('SYSTEM_STATUS')
    cloud_sync = Event[Callable[[bool], None]]('CLOUD_SYNC')
    start_load = Event[Callable[[bool], None]]('START_LOAD')
    splash_load = Event[Callable[[bool], None]]('SPLASH_LOAD')
    system_reboot = Event[Callable[[], None]]('SYSTEM_REBOOT')
    system_shutdown = Event[Callable[[], None]]('SYSTEM_SHUTDOWN')
    renew_jwt = Event[Callable[[], None]]('RENEW_JWT')
    cache_thumbnail = Event[Callable[[bytes], None]]('CACHE_THUMBNAIL')
    update_progress = Event[Callable[[int], None]]('UDPATE_PROGRESS')
    new_benchmark_img = Event[Callable[[np.ndarray], None]]('NEW_BENCHMARK_IMG')
    o2_loader = Event[Callable[[bool], None]]('O2_LOADER')
    co2_loader = Event[Callable[[bool], None]]('CO2_LOADER')
    temp_loader = Event[Callable[[bool], None]]('TEMP_LOADER')
    # imaging
    fl_cooldown = Event[Callable[[], None]]('FL_COOLDOWN')
    start_benchmark = Event[Callable[[str], None]]('START_BENCHMARK')
    end_benchmark = Event[Callable[[], None]]('END_BENCHMARK')
    benchmark_image = Event[Callable[[np.ndarray], None]]('BENCHMARK_START')
    # refresh flags
    new_protocol = Event[Callable[[], None]]('NEW_PROTOCOL')
    new_device = Event[Callable[[], None]]('NEW_DEVICE')
    new_experiment = Event[Callable[[], None]]('NEW_EXPERIMENT')
    # user set arduino commands
    aux_duty = Event[Callable[[str, Union[float, int]], None]]('AUX_DUTY')
    op_mode = Event[Callable[[str, Union[float, int]], None]]('OP_MODE')
    fan_duty = Event[Callable[[str, Union[float, int]], None]]('FAN_DUTY')
    co2_calibration = Event[Callable[[], None]]('CO2_CALIBRATION')
    # AMQP
    amqp_publish = Event[Callable[[str, Dict[str, Any]], None]]('AMQP_PUBLISH')
    amqp_subscribe = Event[Callable[[str, Dict[str, Any]], None]]('AMQP_SUBSCRIBE')
    # pipelines
    preview_pipeline = Pipeline("PREVIEW", 2)
    thumbnail_pipeline = Pipeline("THUMBNAIL", 2)
    avatar_pipeline = Pipeline("AVATAR", 3)
    registration_pipeline = Pipeline("REGISTRATION", 3)
    capture_pipeline = Pipeline("CAPTURE", 3)
