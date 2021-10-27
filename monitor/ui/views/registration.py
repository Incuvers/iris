#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Registration
============
Modified: 2021-07

Dependencies:
-------------
```
import pygame

from monitor.ui.components.widget import Widget
from monitor.ui.components.text_box import TextBox
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uisr
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import pygame

from monitor.ui.components.widget import Widget
from monitor.ui.components.text_box import TextBox
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis


class Registration(Widget):

    def __init__(self, registration_key, surface_height, surface_width):
        # register pipeline stage
        events.registration_pipeline.stage(self.set_registration_key, 2)
        self.registration_key = registration_key
        self.width = surface_width
        self.height = surface_height
        self.header_box_height = 100
        self.logo_surf = pygame.image.load(uis.IRIS).convert_alpha()
        scaling = 0.30
        self.logo_surf = pygame.transform.smoothscale(
            self.logo_surf,
            (int(scaling * self.logo_surf.get_width()), int(scaling * self.logo_surf.get_height()))
        )
        self.instructions_box_height = 200
        self.instructions_box = TextBox(
            self.width - 2 * uis.PADDING,
            self.instructions_box_height,
            text="Register using the link and key provided below:",
            fs_min=10,
            fs_max=50,
            justify="center"
        )
        self.url_box_height = 60
        self.url_box = TextBox(
            height=self.url_box_height,
            width=self.width - 2 * uis.PADDING,
            text="lab.incuvers.com",
            fs_min=10,
            fs_max=50,
            color=uis.LINK_COLOR,
            justify="center"
        )
        self.registration_height = 200
        self.registration = TextBox(
            width=self.width - 2 * uis.PADDING,
            height=self.registration_height,
            text=self.registration_key,
            fs_min=10,
            fs_max=100,
            justify="center"
        )
        self.load_icon = LoadingWheel(
            centering=(300, 770),
            scaling=(50, 50)
        )
        self.load_icon.start()

        self.surf = pygame.Surface((self.width, self.height)) # type: ignore
        self.font_path = uis.FONT_PATH
        self.redraw()

    def set_registration_key(self, registration_key: str):
        self.registration_key = registration_key
        self.registration.update_text(registration_key)
        self.load_icon.stop()

    def redraw(self):
        self.surf.fill(uis.WIDGET_EDGE)
        pygame.draw.rect(self.surf,
                         uis.WIDGET_BACKGROUND,
                         pygame.Rect(uis.PADDING,
                                     uis.PADDING,
                                     self.width - 2 * uis.PADDING,
                                     self.height - 2 * uis.PADDING))
        # compute y offsets
        y_offset = 125
        # render instructions
        self.surf.blit(self.logo_surf, ((self.width - self.logo_surf.get_width()) / 2, y_offset))

        y_offset = 350
        # render instructions
        ins_surf = self.instructions_box.redraw()
        for surface in ins_surf:
            self.surf.blit(surface, (super()._x_center(surface), y_offset))
            y_offset += int(self.instructions_box.font_size * 1.4)

        y_offset = 550
        # render url
        url_surface = self.url_box.redraw()
        for surface in url_surface:
            self.surf.blit(surface, (super()._x_center(surface), y_offset))
            y_offset += int(self.instructions_box.font_size * 1.4)

        y_offset = 700
        # render key
        registration_surf = self.registration.redraw()
        for surface in registration_surf:
            self.surf.blit(surface, (super()._x_center(surface), y_offset))

        # while loading icon is enabled blit it.
        surfs = self.load_icon.update()
        if surfs is not None:
            self.surf.blit(surfs[0], surfs[1])

    def compute_y_offset(self, s: int, ts: int, h: list) -> list:
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

    def _render_text(self, registration_key, font_size, color):
        font = pygame.font.Font(self.font_path, font_size)
        return font.render(registration_key, True, color)
