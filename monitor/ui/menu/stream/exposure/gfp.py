# -*- coding: utf-8 -*-
"""
GFP Exposure Menu
=================
Modified: 2021-07

Dependencies:
-------------
```
import logging
import monitor.imaging.constants as IC

from monitor.models.experiment import Experiment
from monitor.exceptions.microscope import MicroscopeError
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.ui.menu.stream.exposure.exposure import ExposureMenu
from monitor.microscope.microscope import Microscope as scope
from monitor.microscope.camera.stream_pipeline import StreamPipeline
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import monitor.imaging.constants as IC

from monitor.models.experiment import Experiment
from monitor.exceptions.microscope import MicroscopeError
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.ui.menu.stream.exposure.exposure import ExposureMenu
from monitor.microscope.microscope import Microscope as scope
from monitor.microscope.camera.stream_pipeline import StreamPipeline


class GFPExposureMenu(ExposureMenu):

    def __init__(self, main, surface, channel: StreamPipeline, min_exposure: int, max_exposure: int):
        self._logger = logging.getLogger(__name__)
        super().__init__(main, surface, channel, min_exposure=min_exposure, max_exposure=max_exposure)
        with StateManager() as state:
            state.subscribe(ImagingProfile, self.update_profile)
            state.subscribe(Experiment, self._cancel)

    async def update_profile(self, imaging_profile: ImagingProfile) -> None:
        self.current_exposure_grade = IC.gfp_exposure_to_grade(imaging_profile.gfp_exposure)
        self.knob.set_value(self.current_exposure_grade)

    def _check_value(self, value: int, c=None, **kwargs):
        """
        Callback on value change
        """
        # always update the current exposure
        # pause the preview if it is not already paused
        if not self.preview.paused:
            self.preview.pause()
        # generate runtime ip and update
        with StateManager() as state:
            imaging_profile = state.imaging_profile
            imaging_profile.gfp_exposure = IC.gfp_grade_to_exposure(value)
            # commit to state without caching
            state.commit(imaging_profile, cache=False)
        self._logger.debug("Exposure: %s", value)
        self.current_exposure_grade = value

    def _confirm_value(self):
        """
        When the user clicks OK
        """
        self.knob.set_value(self.current_exposure_grade)
        # conditional to check if cooldown is required (was burnout reached)
        if scope.fluorescence.initialized and scope.fluorescence.cooldown:
            events.fl_cooldown.trigger()
        # save current imaging settings to cache
        with StateManager() as state:
            state.commit(state.imaging_profile, cache=True)
        scope.gfp_stream_ctrl(flag=False)
        self.menu.reset(1)

    @tm.threaded(daemon=True)
    def enable_microscope(self) -> None:
        """
        Start stream
        """
        try:
            scope.gfp_stream_ctrl(flag=True)
        except MicroscopeError as exc:
            self._logger.critical("Microscope failed to activate: %s", exc)
            events.system_status.trigger(status=uis.STATUS_ALERT)
        else:
            self._logger.debug("Successfully started microscope stream")

    async def _cancel(self, experiment: Experiment):
        """
        Edge case where user is streaming and an experiment is cached. Do not cache
        the current settings as the inbound experiment will have its own settings.
        """
        if self.active:
            scope.gfp_stream_ctrl(flag=False)
            self._logger.warning(
                "Kicked out of the gfp exposure menu as an experiment %s is iminent", experiment.id)
            self.menu.reset(1)
