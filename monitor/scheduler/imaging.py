#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Imaging Scheduler
=================
Modified: 2021-04

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
import logging
from datetime import datetime, timezone

from monitor.models.experiment import Experiment
from monitor.scheduler.scheduler import Scheduler
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import PropertyCondition, StateManager


class ImagingScheduler(Scheduler):

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        super().__init__()
        self._logger.info("Imaging schedule runner active")
        with StateManager() as state:
            state.subscribe_property(
                _type=Experiment,
                _property=PropertyCondition[Experiment](
                    trigger=lambda old_experiment, new_experiment:
                        old_experiment.id != new_experiment.id and new_experiment.stop_at is None,
                    callback=self._schedule,
                    callback_on_init=True
                )
            )
            # stop_at being set is an indicator of experiment cancellation
            state.subscribe_property(
                _type=Experiment,
                _property=PropertyCondition[Experiment](
                    trigger=lambda old_experiment, new_experiment:
                        old_experiment.id == new_experiment.id and new_experiment.stop_at is not None,
                    callback=self.cleanup,
                )
            )
        self._logger.info("Instantiation successful.")

    async def _schedule(self, experiment: Experiment):
        """
        Schedules image capture events
        """
        now = math.ceil(datetime.now(timezone.utc).timestamp())
        start = math.ceil(experiment.start_at.timestamp())
        end = math.ceil(experiment.end_at.timestamp())
        if end < now or experiment.stop_at is not None:
            self._logger.info("%s expired. Skipping scheduling", experiment)
            return
        self.purge_queue()
        self._logger.debug("Loading imaging events for %s", experiment)
        # collect scheduling parameters from active experiment in units of minutes (convert to seconds)
        interval = experiment.image_capture_interval * 60
        # compute datetime objects epoch
        self._logger.debug("Start UTC: %s", experiment.start_at)
        self._logger.debug("Start Epoch: %s", start)
        self._logger.debug("End UTC: %s", experiment.end_at)
        self._logger.debug("End Epoch: %s", end)
        # compute current epoch (ensure relative offset remains constant during scheduling)
        self._logger.debug("Now UTC: %s", datetime.now(timezone.utc))
        self._logger.debug("Now Epoch: %s", now)
        delta = start
        self._logger.debug("Experiment captures scheduled to start in T-%s", start - now)
        while delta < end:
            if delta >= now:
                self._logger.debug("Absolute Epoch Time Entry: %s", delta)
                # populate an image capture event trigger
                self.populate(delta, 0, events.capture_pipeline.begin)
            delta += interval
        self._logger.debug(self)

    async def cleanup(self, experiment: Experiment):
        """
        Clear the scheduler queue
        """
        self.purge_queue()
        self._logger.info("Successfully purged the experiment imaging queue for: %s", experiment)
        self._logger.debug(self)
