#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Protocol Scheduler
==================
Modified: 2020-05-22

Dependencies:
-------------
```
import numpy as np
import time
import logging.config
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import math
import time
import logging
from typing import Union
from datetime import datetime, timezone

from monitor.models.experiment import Experiment
from monitor.models.protocol import Protocol
from monitor.environment.state_manager import StateManager
from monitor.environment.state_manager import PropertyCondition
from monitor.scheduler.scheduler import Scheduler
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings


class SetpointScheduler(Scheduler):

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        super().__init__()
        self._logger.info("Setpoint schedule runner active")
        # Setup property conditions
        with StateManager() as state:
            # All protocol changes should be scheduled / re-scheduled
            state.subscribe(Protocol, self._schedule)
            state.subscribe_property(
                _type=Experiment,
                _property=PropertyCondition[Experiment](
                    trigger=lambda old_experiment, new_experiment:
                        old_experiment.id == new_experiment.id and not new_experiment.active,
                    callback=self.cleanup,
                )
            )
        self._logger.info("Instantiation successful.")

    async def _schedule(self, protocol: Protocol):
        """
        Schedules setpoint events
        :param priority: integer defining the layer which the protocol resides
        """
        with StateManager() as state:
            experiment = state.experiment
        exp_end = math.ceil(experiment.end_at.timestamp())
        now = math.ceil(datetime.now(timezone.utc).timestamp())
        # prechecks
        if experiment.protocol_id != protocol.id:
            self._logger.warning("%s and %s mismatch skipping setpoint scheduling", experiment, protocol)
            return
        if exp_end < now or experiment.stop_at is not None:
            self._logger.info("%s expired. Skipping scheduling", experiment)
            return
        self.purge_queue()
        # repeats in the context of loops
        self._logger.debug("Loading setpoints events for %s", protocol)
        repeats = protocol.repeats
        self._logger.debug("Repeat: %s", repeats)
        # sort setpoints by setpoint indices
        setpoints = sorted(protocol.setpoints, key=lambda x: x['index'])
        self._logger.debug("Setpoints: %s", setpoints)
        # compute current epoch (ensure relative offset remains constant during scheduling)
        self._logger.debug("Now UTC: %s", datetime.now(timezone.utc))
        self._logger.debug("Now Epoch: %s", now)
        self._logger.debug("Start Time Epoch: %s", math.ceil(experiment.start_at.timestamp()))
        # convert ISO string in UTC to a datetime object and calculate its epoch
        start = math.ceil(experiment.start_at.timestamp())
        delta = start
        for _ in range(repeats):
            for setpoint in setpoints:
                self._logger.debug(
                    "Setpoint TP: %s CP: %s OP: %s | Now: %s, Delta: %s, Delta + Duration: %s",
                    setpoint['TP'], setpoint['OP'], setpoint['CP'], now, delta, delta + setpoint['duration'])
                # check if the setpoint is in the future or if we are in its interval
                if delta >= now or (delta + setpoint['duration']) >= now:
                    # populate a setpoint event trigger for each setpoint
                    # relative time recomputes now and has slight offsets between population events
                    self.populate(delta, 1, self._trigger,
                                  setpoint['TP'], setpoint['OP'], setpoint['CP'])
                delta += int(setpoint['duration'])
        self.populate(exp_end, 0, self.purge_queue)
        self._logger.debug(self)

    def _trigger(self, tp: Union[int, float], op: Union[int, float], cp: Union[int, float]):
        """
        Update trigger setpoints
        """
        self._logger.debug(self)
        self._logger.info("Triggering setpoint conditions: TP: %s, OP: %s, CP: %s", tp, op, cp)
        with StateManager() as state:    
            icb = state.icb
            while not icb.initialized:
                self._logger.info("ICB state not initialized. Waiting for icb initialization ...")
                time.sleep(1)
                icb = state.icb
            # apply the new setpoint state to the system
            icb.cp = cp
            icb.op = op
            icb.tp = tp
            result = state.commit(icb)
        if not result:
            self._logger.critical("Setpoint change for scheduled protocol events not accepted")
            events.system_status.trigger(status=UISettings.STATUS_ALERT)

    async def cleanup(self, experiment: Experiment):
        """
        Clear the scheduler queue
        """
        # purge the queue in case of experiment cancellation
        self.purge_queue()
        self._logger.info("Successfully purged the experiment protocol queue for: %s", experiment)
        self._logger.debug(self)
