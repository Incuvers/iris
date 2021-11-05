# -*- coding: utf-8 -*-
"""
Experiment
==========
Modified: 2021-11

Dependencies:
-------------
```
import os
import math
import pygame
import logging
from datetime import datetime
from pathlib import Path

from monitor.ui.components.widget import Widget
from monitor.ui.components.text_box import TextBox
from monitor.ui.components.progress_bar import ProgressBar
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.environment.state_manager import StateManager
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis

```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import math
import pygame
import logging
from datetime import datetime
from pathlib import Path

from monitor.ui.components.widget import Widget
from monitor.ui.components.text_box import TextBox
from monitor.ui.components.progress_bar import ProgressBar
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.environment.state_manager import StateManager
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis


class ExperimentWidget(Widget):

    """
    Info widget for showing experiment details
    """

    def __init__(self, surface_height: int, surface_width: int):
        """
        init
        """
        self._logger = logging.getLogger(__name__)
        self.width = surface_width
        self.height = int(uis.EW_HEIGHT_RATIO * surface_height)
        self._logger.debug("Experiment Widget width: %s, height: %s", self.width, self.height)
        self.surf = pygame.Surface((self.width, self.height))  # type: ignore
        self.progress_bar = ProgressBar(self.width, 25, text="Experiment Progress: ")
        self.preview = None
        scaling = 0.25
        self.logo_surf = pygame.image.load(uis.IRIS).convert_alpha()
        self.logo_surf = pygame.transform.smoothscale(
            self.logo_surf,
            (int(scaling * self.logo_surf.get_width()), int(scaling * self.logo_surf.get_height()))
        )
        self.elapsed = TextBox(
            width=self.width - 2 * uis.PADDING,
            height=self.height - 2 * uis.PADDING,
            text='',
            fs_min=10,
            fs_max=30
        )
        self.capture = TextBox(
            width=self.width - 2 * uis.PADDING,
            height=self.height - 2 * uis.PADDING,
            text='',
            fs_min=10,
            fs_max=30
        )
        self.queued = TextBox(
            width=self.width - 2 * uis.PADDING,
            height=self.height - 2 * uis.PADDING,
            text='',
            fs_min=10,
            fs_max=30
        )
        self.countdown = TextBox(
            width=self.width - 2 * uis.PADDING,
            height=self.height - 2 * uis.PADDING,
            text='',
            fs_min=10,
            fs_max=50,
            color=uis.INCUVERS_BLUE
        )
        self.image_loader = LoadingWheel(
            centering=(self.width * 3 // 4, self.height // 2),
            scaling=(50, 50),
            low_res=True
        )
        self.comp_loader = LoadingWheel(
            centering=(self.width // 2, self.height // 2 - 15),
            scaling=(50, 50)
        )
        self.font_path = uis.FONT_PATH
        self.thumbnail_path = os.environ.get('COMMON', default='/etc/iris') + '/thumbnail.png'
        # always render thumbnail if it exists
        if Path(self.thumbnail_path).exists():
            self.render_dpc()
        self.redraw()
        events.capture_pipeline.stage(self.acquiring, 0)
        events.thumbnail_pipeline.stage(self.render_dpc, 1)
        self._logger.info("Instantiation successful.")

    def acquiring(self):
        self.image_loader.start()

    def render_dpc(self):
        """
        Thumbnail preview is available in COMMON; render it to the component
        """
        scaling = 1.3
        try:
            self.preview = pygame.image.load(self.thumbnail_path)
            self.preview = pygame.transform.scale(
                self.preview,
                (int(scaling * self.preview.get_width()), int(scaling * self.preview.get_height()))
            )
        except pygame.error as exc:  # type: ignore
            self.preview = None
            self._logger.warning("Thumbnail image is corrupted: setting to None: %s", exc)
        finally:
            self.image_loader.stop()

    def redraw(self):
        self.surf.fill(uis.WIDGET_EDGE)
        pygame.draw.rect(self.surf,
                         uis.WIDGET_BACKGROUND,
                         pygame.Rect(uis.PADDING,
                                     uis.PADDING,
                                     self.width - 2 * uis.PADDING,
                                     self.height - 2 * uis.PADDING))
        with StateManager() as state:
            experiment = state.experiment
        delta = math.ceil(experiment.start_at.timestamp() - datetime.now().timestamp())
        # check if the experiment has a start time in the future
        if experiment.stop_at is None and not experiment.active and delta > 0:
            self.preview = None
            # perform time calculations
            # counters must be in units int (ceil to preserve inbetween time)
            # experiment queued
            hours, remainder = divmod(delta, 60 * 60)
            minutes, seconds = divmod(remainder, 60)
            self.queued.update_text("Experiment '{}' In:".format(experiment.name))
            self.countdown.update_text("{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds))
            queued_surf = self.queued.redraw()
            for surface in queued_surf:
                self.surf.blit(surface, ((self.width - surface.get_width()) / 2, 15))
            countdown_surf = self.countdown.redraw()
            for surface in countdown_surf:
                self.surf.blit(surface, ((self.width - surface.get_width()) / 2, 60))
        # experiment active
        elif experiment.active:
            capture_interval = experiment.image_capture_interval
            duration = experiment.duration
            delta = abs(delta)
            if (delta / duration) * 100 > 100: percent = 100
            else: percent = int((delta / duration) * 100)
            self.progress_bar.update(percent)
            self.progress_bar.redraw()
            self.surf.blit(self.progress_bar.get_surface(), (0, 0))
            hours, remainder = divmod(delta, 60 * 60)
            minutes, seconds = divmod(remainder, 60)
            self.elapsed.update_text(
                "Elapsed: {:02d}:{:02d}:{:02d}".format(hours, minutes, seconds))
            # careful to convert capture interval (in minutes) to epoch digest (seconds)
            if (experiment.end_at.timestamp() - capture_interval * 60) < datetime.now().timestamp()\
                    < experiment.end_at.timestamp():
                val = 0  # no capture on final interval
            else:
                val = math.ceil(delta % (capture_interval * 60))
                val = (capture_interval * 60) - val
            hours, remainder = divmod(val, 60 * 60)
            minutes, seconds = divmod(remainder, 60)
            self.capture.update_text(
                "Capture: {:02d}:{:02d}:{:02d}".format(hours, minutes, seconds))
            elapsed_surf = self.elapsed.redraw()
            for surface in elapsed_surf:
                self.surf.blit(surface, (25, 40))
            capture_surf = self.capture.redraw()
            for surface in capture_surf:
                self.surf.blit(surface, (25, 90))
            # render dpc preview if available
            if self.preview is None:
                pygame.draw.rect(
                    self.surf,
                    uis.WIDGET_EDGE,
                    pygame.Rect(
                        self.width // 2,
                        25,
                        self.width,
                        self.height
                    )
                )
            else:
                prev_width, prev_height = self.preview.get_width(), self.preview.get_height()
                self.surf.unlock()
                try:
                    self.surf.blit(self.preview,
                                   (self.width / 2, 25),
                                   ((prev_width - 288) / 2,
                                    (prev_height - 155) / 2,
                                    288,
                                    155))
                except pygame.error as exc:  # type: ignore
                    self._logger.warning(
                        "Pygame encountered an error while trying to blit surface: %s", exc)
            # render loading wheel
            load_wheel = self.image_loader.update()
            if load_wheel is not None:
                self.surf.blit(load_wheel[0], load_wheel[1])
        # if not experiment.is_active
        else:
            self.surf.blit(self.logo_surf, ((self.width - self.logo_surf.get_width()) / 2, 15))
