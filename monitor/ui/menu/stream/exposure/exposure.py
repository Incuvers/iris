# -*- coding: utf-8 -*-
"""
Exposure Menu
=============
Modified: 2021-05

Dependencies:
-------------
```
from typing import Optional
from monitor.ui.menu.pgm.menu import Menu
from monitor.models.experiment import Experiment
from monitor.ui.static.settings import UISettings as uis
from monitor.models.imaging_profile import ImagingProfile
from monitor.microscope.camera.gst_pipeline import GSTPipeline
from monitor.ui.components.stream_preview import StreamPreview
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""


from monitor.ui.menu.pgm.menu import Menu
from monitor.models.experiment import Experiment
from monitor.ui.static.settings import UISettings as uis
from monitor.models.imaging_profile import ImagingProfile
from monitor.microscope.camera.stream_pipeline import StreamPipeline
from monitor.ui.components.stream_preview import StreamPreview


class ExposureMenu:

    def __init__(self, main, surface, pipeline: StreamPipeline, min_exposure=0, max_exposure=100):
        self.main = main
        self.main_surface = surface
        self.active = False
        self.menu_height = 300
        self.preview = StreamPreview(uis.WIDTH, uis.HEIGHT - self.menu_height, pipeline, stats=True)
        # initialize exposure counter
        self.current_exposure_grade = 0
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
            option_shadow=False,
            rect_width=4,
            title="Adjust Exposure",
            title_offsety=0,
            window_height=self.menu_height,
            window_width=uis.WIDTH,
        )
        self.confim_option = self.menu.add_option('OK', self._confirm_value)
        self.knob = self.menu.add_knob_selector(
            title="",
            min_val=min_exposure,
            max_val=max_exposure,
            start_val=self.current_exposure_grade,
            alarm_color=(255, 0, 0),
            incr=1,  # default increment value
            speed_thresh=0.6,
            selector_id='',
            off_on_limit=False,
            sfmt='{} %',
            onchange=self._check_value,
            onreturn=self._try_value,
            write_on_console=False
        )
        # update uninitialized current exposure values with microscope validated ip
        self.menu.disable()

    def enable_microscope(self) -> None:
        raise NotImplementedError

    async def update_profile(self, imaging_profile: ImagingProfile) -> None:
        raise NotImplementedError

    def draw_preview(self):
        """
        """
        self.preview.redraw()
        self.main_surface.blit(self.preview.get_surface(),
                               (0, uis.HEIGHT - self.preview.height))

    def _check_value(self, value: int, c=None, **kwargs):
        """ Callback on value change """
        raise NotImplementedError

    def _try_value(self, value, c=None, **kwargs):
        """
        When the user clicks out of the knob selector
        """
        self.main._select(self.main._actual._index - 2)

    def _confirm_value(self):
        """
        When the user clicks OK
        """
        raise NotImplementedError

    async def _cancel(self, experiment: Experiment):
        raise NotImplementedError

    def _bgfun(self):
        pass
