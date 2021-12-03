# -*- coding: utf-8 -*-
"""
Phase Exposure Menu
===================
Modified: 2021-07

Dependencies:
-------------
```
import logging
from typing import Optional
import monitor.imaging.constants as IC

from monitor.microscope.microscope import Microscope as scope
from monitor.microscope.camera.gst_pipeline import GSTPipeline
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile
from monitor.exceptions.microscope import MicroscopeError
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import StateManager
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.menu.stream.exposure.exposure import ExposureMenu
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import monitor.imaging.constants as IC

from monitor.microscope.camera.stream_pipeline import StreamPipeline
from monitor.microscope.microscope import Microscope as scope
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile
from monitor.exceptions.microscope import MicroscopeError
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import PropertyCondition, StateManager
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.menu.stream.exposure.exposure import ExposureMenu


class PhaseExposureMenu(ExposureMenu):

    def __init__(self, main, surface, channel: StreamPipeline, min_exposure: int, max_exposure: int):
        self._logger = logging.getLogger(__name__)
        super().__init__(main, surface, channel, min_exposure=min_exposure, max_exposure=max_exposure)
        with StateManager() as state:
            state.subscribe_property(
                _type=ImagingProfile,
                _property=PropertyCondition[ImagingProfile](
                    trigger=lambda old_ip, new_ip: old_ip.dpc_exposure != new_ip.dpc_exposure,
                    callback=self.update_profile,
                    callback_on_init=True
                )
            )
            state.subscribe_property(
                _type=Experiment,
                _property=PropertyCondition[Experiment](
                    trigger=lambda old_exp, new_exp: old_exp.id != new_exp.id,
                    callback=self._cancel
                )
            )

    async def update_profile(self, imaging_profile: ImagingProfile) -> None:
        self.current_exposure_grade = IC.dpc_exposure_to_grade(imaging_profile.dpc_exposure)
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
            imaging_profile.dpc_exposure = IC.dpc_grade_to_exposure(value)
            # commit to state without caching
            state.commit(imaging_profile, cache=False)
        self._logger.debug("Exposure: %s", value)
        self.current_exposure_grade = value

    def _confirm_value(self):
        """
        When the user clicks OK
        """
        self.knob.set_value(self.current_exposure_grade)
        # save current imaging settings to cache
        with StateManager() as state:
            state.commit(state.imaging_profile, cache=True)
        scope.exposure_stream_ctrl(flag=False)
        self.menu.reset(1)

    @tm.threaded(daemon=True)
    def enable_microscope(self) -> None:
        """
        Start stream
        """
        try:
            scope.exposure_stream_ctrl(flag=True)
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
            scope.exposure_stream_ctrl(flag=False)
            self._logger.warning(
                "Kicked out of the exposure menu as an experiment %s is iminent", experiment.id)
            self.menu.reset(1)
