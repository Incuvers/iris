# -*- coding: utf-8 -*-
"""
Loading Canvas
==============
Modified: 2021-07

Dependencies:
-------------
```
import pygame
import numpy as np

from monitor.ui.components.widget import Widget
from monitor.ui.components.text_box import TextBox
from monitor.ui.components.progress_bar import ProgressBar
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import pygame
import numpy as np

from monitor.ui.components.widget import Widget
from monitor.ui.components.text_box import TextBox
from monitor.ui.components.progress_bar import ProgressBar
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis


class Loading(Widget):

    def __init__(self, surface_height: int, surface_width: int):
        self.width = surface_width
        self.height = surface_height
        self.show_benchmark_image = False
        self.show_status = False
        self.show_pv = False
        self.system_status_surf = pygame.image.load(uis.STATUS_OK).convert_alpha()
        self.status_textbox_height = 100
        self.status_textbox = TextBox(
            width=self.width - 2 * uis.PADDING,
            height=self.status_textbox_height,
            text='',
            fs_min=5,
            fs_max=30,
            justify="center"
        )
        self.surf = pygame.Surface((self.width, self.height)) # type: ignore
        self.load_icon = LoadingWheel(
            centering=(300, 500),
            scaling=(50, 50)
        )
        self.load_icon.start()
        scaling = 0.12
        self.logo_surf = pygame.image.load(uis.LOGO).convert_alpha()
        self.logo_surf = pygame.transform.smoothscale(
            self.logo_surf,
            (int(scaling * self.logo_surf.get_width()), int(scaling * self.logo_surf.get_height()))
        )

        scaling_benchmark = 0.14
        self.benchmark_surf = pygame.image.load(uis.LOGO).convert_alpha()
        self.benchmark_surf = pygame.transform.smoothscale(
            self.benchmark_surf,
            (
                int(scaling_benchmark * self.benchmark_surf.get_width()),
                int(scaling_benchmark * self.benchmark_surf.get_height())
            )
        )
        self.pv = ProgressBar(375, 25, text="")
        events.system_status.register(self.set_message, condition=lambda *argv,
                                      **kwargs: False if kwargs.get('msg') is None else True)
        events.start_load.register(self.reset_state,
            condition=lambda *argv: argv[0])
        events.update_progress.register(
            self.set_pv, condition=lambda *argv: True if argv[0] == 0 else False)
        events.new_benchmark_img.register(self.set_benchmark_image)
        self.redraw()

    def reset_state(self, _: bool):
        """
        Only called when load state is changed to false (start of load in)
        """
        self.show_status = False
        self.show_pv = False
        self.load_icon.start()

    def set_pv(self, _: int):
        self.show_pv = True

    def set_message(self, msg: str, status: str = None):
        """ Feedback status indicator for monitor boot """
        self.status_textbox.update_text(msg)
        if status == uis.STATUS_WORKING:
            self.load_icon.start()
            self.show_status = False
        elif status is not None:
            self.show_status = True
            self.load_icon.stop()
            self.system_status_surf = pygame.image.load(status).convert_alpha()
        else:
            self.show_status = False

    def set_benchmark_image(self, generated_benchmark_image: np.ndarray):
        """
        :param generated_benchmark_image is a numpy array that will be rendered on the GUI
        """
        benchmark_image = np.transpose(generated_benchmark_image, (1, 0, 2))
        self.benchmark_surf = pygame.surfarray.make_surface(benchmark_image)
        self.load_icon.stop()
        self.show_benchmark_image = True
        self.redraw()

    def redraw(self):
        self.surf.fill(uis.WIDGET_EDGE)
        pygame.draw.rect(
            self.surf,
            uis.WIDGET_BACKGROUND,
            pygame.Rect(
                uis.PADDING,
                uis.PADDING,
                self.width - 2 * uis.PADDING,
                self.height - 2 * uis.PADDING
            )
        )

        # compute y offsets
        start_offset = 200
        if self.show_benchmark_image:
            # compute y offsets
            y_offsets = self.compute_y_offset(
                start_offset,
                20,
                [self.benchmark_surf.get_height(), self.status_textbox.height]
            )
            self.surf.blit(self.benchmark_surf, (0, 0))

        else:
            y_offsets = self.compute_y_offset(
                start_offset, 300,
                [self.logo_surf.get_height(), self.status_textbox.height]
            )
            # render logo
            self.surf.blit(
                self.logo_surf, ((self.width - self.logo_surf.get_width()) / 2, y_offsets[0]))

        # render wheel
        if self.show_status:
            # show system status icon once load is complete
            self.surf.blit(self.system_status_surf, (280, 500))
        elif self.show_pv:
            self.pv.redraw()
            self.surf.blit(self.pv.get_surface(), (100, 500))
        else:
            load_wheel = self.load_icon.update()
            # while loading icon is enabled blit it.
            if load_wheel is not None:
                self.surf.blit(load_wheel[0], load_wheel[1])

        # render header
        status_surf = self.status_textbox.redraw()
        for surface in status_surf:
            self.surf.blit(surface, ((self.width - surface.get_width()) / 2, y_offsets[1]))

    @staticmethod
    def compute_y_offset(s: int, ts: int, h: list) -> list:
        """
        :param s: starting offset
        :param ts: inter-textbox spacing
        :param h: list of textbox heights in top to bottom order
        """
        offsets = list()
        y = s
        for _, v in enumerate(h):
            offsets.append(y)
            y += v + ts
        return offsets
