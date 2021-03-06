# -*- coding: utf-8 -*-
"""
Gauge
=====
Modified: 2021-07

Dependencies:
-------------
```
import logging
import pygame
from pygame import gfxdraw
from typing import Optional, Tuple
from monitor.ui.components.widget import Widget

from monitor.ui.static.settings import UISettings as uis
from monitor.ui.components.loading_wheel import LoadingWheel
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import pygame  # type: ignore
from pygame import gfxdraw  # type:ignore
from typing import Optional, Tuple
from monitor.ui.components.widget import Widget

from monitor.ui.static.settings import UISettings as uis
from monitor.ui.components.loading_wheel import LoadingWheel


class Gauge(Widget):

    VALUE = '...'

    def __init__(self, name: str, width: int, height: int):
        self._logger = logging.getLogger(__name__)
        self.title_string = name
        self.width = width
        self.height = height
        self._logger.info("%s gauge width: %s height: %s", name, width, height)
        self.circ_radius = int(self.width // 2 * .8)  # get as percent of width
        self.gauge_loader = LoadingWheel(
            centering=(self.width // 2, self.height - self.circ_radius - uis.GAUGE_TEXT_PADDING),
            scaling=(50, 50),
            timeout=15,
            low_res=False
        )
        self.setpoint_loader = LoadingWheel(
            centering=(170, 265),
            scaling=(30, 30),
            timeout=15,
            low_res=True
        )
        self.load_state: bool = False
        self.load_set: bool = False
        self.surf = pygame.Surface((self.width, self.height))  # type:ignore
        self.font_path = uis.FONT_PATH
        self.redraw()

    def _circle(self, surf, color, x, y, radius):
        """
        :param surf: surface on which to draw
        :param color: color of circle
        :param x: x coordinate
        :param y: y coordinate
        :param radius: radius
        :return: None
        """
        gfxdraw.aacircle(surf, x, y, radius, color)
        gfxdraw.filled_circle(surf, x, y, radius, color)

    def get_state(self) -> Tuple[bool, str, str]:
        raise NotImplementedError

    def draw_gauge(self, setpoint: Optional[str], value: Optional[str], disabled: bool) -> None:
        # constuct
        if disabled:
            circle_color = uis.DISABLED_OBJ
            title_text_color = uis.DISABLED_TEXT
            gauge_text_color = uis.DISABLED_TEXT
        else:
            circle_color = uis.INCUVERS_BLUE
            title_text_color = uis.INCUVERS_WHITE
            gauge_text_color = uis.INCUVERS_BLUE

        self.surf.fill(uis.WIDGET_EDGE)
        pygame.draw.rect(self.surf,
                         uis.WIDGET_BACKGROUND,
                         pygame.Rect(uis.PADDING,
                                     uis.PADDING,
                                     self.width - 2 * uis.PADDING,
                                     self.height - 2 * uis.PADDING))
        x = self.width // 2
        y = self.height - self.circ_radius - uis.GAUGE_TEXT_PADDING
        self._circle(self.surf, circle_color, x, y,
                     self.circ_radius)
        self._circle(self.surf, uis.INCUVERS_DARK_GREY, x, y,
                     self.circ_radius - 10)
        self._circle(self.surf, uis.INCUVERS_LIGHT_GREY, x, y,
                     self.circ_radius - 20)
        font_size = 35
        y_offset = uis.GAUGE_TEXT_PADDING
        # display the setpoint depending on the loading state
        if setpoint is None or self.load_state:
            self.setpoint_loader.stop()
            self.gauge_loader.start()
            sp_str = ''
            value = ''  # override value
        elif self.load_set:
            self.gauge_loader.stop()
            self.setpoint_loader.start()
            sp_str = 'Set:      '  # override setpoint
        else:  # loading string (space for loading wheel)
            self.gauge_loader.stop()
            self.setpoint_loader.stop()
            sp_str = 'Set: {}'.format(setpoint)
        self._render_text(self.title_string, y_offset, font_size, title_text_color)
        font_size = 45
        y_offset = self.height - (self.circ_radius + uis.GAUGE_TEXT_PADDING) - font_size
        if value is not None:
            self._render_text(value, y_offset, font_size, gauge_text_color)
        font_size = 25
        y_offset = self.height - (self.circ_radius + uis.GAUGE_TEXT_PADDING) + font_size
        self._render_text(sp_str, y_offset, font_size, gauge_text_color)

    def redraw(self):
        disabled, setpoint, value = self.get_state()
        if value is None:
            self.gauge_loader.start()
        else:
            self.gauge_loader.stop()
        self.draw_gauge(setpoint, value, disabled=disabled)
        # while loading icon is enabled blit it.
        surfs = self.setpoint_loader.update()
        if surfs is not None:
            self.surf.blit(surfs[0], surfs[1])
        # init loading wheel
        surfs = self.gauge_loader.update()
        if surfs is not None:
            self.surf.blit(surfs[0], surfs[1])
