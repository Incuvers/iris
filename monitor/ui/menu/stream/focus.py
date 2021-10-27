# -*- coding: utf-8 -*-
"""
Image Stream Menu
=================
Modified: 2021-07

Dependencies:
-------------
```
import logging
from typing import Optional

from monitor.models.experiment import Experiment
from monitor.environment.state_manager import StateManager
from monitor.microscope.camera.gst_pipeline import GSTPipeline
from monitor.ui.menu.pgm.menu import Menu
from monitor.microscope.microscope import Microscope as scope
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.components.stream_preview import StreamPreview
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging

from monitor.models.experiment import Experiment
from monitor.environment.state_manager import PropertyCondition, StateManager
from monitor.ui.menu.pgm.menu import Menu
from monitor.microscope.camera.stream_pipeline import StreamPipeline
from monitor.microscope.microscope import Microscope as scope
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.components.stream_preview import StreamPreview


class FocusMenu:

    def __init__(self, main, surface, channel: StreamPipeline):
        self._logger = logging.getLogger(__name__)
        with StateManager() as state:
            state.subscribe_property(
                _type=Experiment,
                _property=PropertyCondition[Experiment](
                    trigger=lambda old_exp, new_exp: old_exp.id != new_exp.id,
                    callback=self._cancel
                )
            )
        self.acquisition = False
        self.main = main
        self.main_surface = surface
        self.menu_height = 300
        self.active = False
        height = uis.HEIGHT - self.menu_height
        self.preview = StreamPreview(uis.WIDTH, height, channel, stats=True)
        self.menu = Menu(
            surface=surface,
            dopause=True,
            bgfun=self._bgfun,
            font=uis.FONT_PATH,
            menu_alpha=100,
            menu_color=uis.MENU_COLOR,
            menu_color_title=uis.MENU_COLOR_TITLE,
            color_selected=uis.COLOR_SELECTED,
            menu_height=self.menu_height,
            menu_width=uis.WIDTH,
            draw_region_y=63,
            option_margin=20,
            option_shadow=False,
            rect_width=4,
            title="Adjust Focus",
            title_offsety=0,
            window_height=self.menu_height,
            window_width=uis.WIDTH,
        )
        self.return_option = self.menu.add_option('Return', self._return)

    def enable_microscope(self):
        try:
            scope.focus_stream_ctrl(flag=True)
        except TypeError as exc:
            self._logger.critical("GST pipeline crashed: %s", exc)
            events.system_status.trigger(status=uis.STATUS_ALERT)
        else:
            self._logger.debug("Successfully started microscope stream")

    def draw_preview(self):
        self.preview.redraw()
        self.main_surface.blit(self.preview.get_surface(),
                               (0, uis.HEIGHT - self.preview.height))

    def _return(self):
        scope.focus_stream_ctrl(flag=False)
        self.menu.reset(1)

    async def _cancel(self, experiment: Experiment) -> None:
        if self.active:
            scope.focus_stream_ctrl(flag=False)
            self._logger.warning(
                "Kicked out of the focus menu as an experiment: %s is iminent", experiment)
            self.menu.reset(1)

    def _bgfun(self):
        pass
