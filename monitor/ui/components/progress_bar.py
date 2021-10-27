# -*- coding: utf-8 -*-
"""
Progress Bar
============
Modified: 2021-07

Dependancies
------------
```
import pygame
import numpy as np
from typing import Optional

from monitor.ui.components.widget import Widget
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import pygame
import numpy as np
from typing import Optional

from monitor.ui.components.widget import Widget
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis


class ProgressBar(Widget):

    def __init__(self, width: int, height: int, text: str = ""):
        self.width = width
        self.height = height
        self.surf = pygame.Surface((self.width, self.height))  # type: ignore
        self.font_path = uis.FONT_PATH
        self.text = text
        self.fill_color = uis.PROGRESS_BAR_FILL

        # These are for the color mapping
        self.map_is_initialized = False
        self.coef_m = None
        self.coef_b = None
        text_old = uis.INCUVERS_WHITE
        text_new = uis.INCUVERS_BLACK
        self._init_map_coefficients(
            uis.WIDGET_BACKGROUND,
            self.fill_color,
            text_old,
            text_new
        )
        self.percent_complete = 0.0
        self.redraw()
        events.update_progress.register(self.update)

    def update(self, percent_complete: int):
        self.percent_complete = percent_complete

    def redraw(self):
        self.surf.fill(uis.WIDGET_EDGE)
        pygame.draw.rect(self.surf,
                         uis.WIDGET_BACKGROUND,
                         pygame.Rect(uis.PADDING,
                                     uis.PADDING,
                                     self.width - 2 * uis.PADDING,
                                     self.height - 2 * uis.PADDING))

        font_size = 15
        font = pygame.font.Font(self.font_path, font_size)
        text_surf = font.render("{}{}%".format(self.text, round(self.percent_complete, 1)),
                                True,
                                uis.INCUVERS_WHITE,
                                uis.WIDGET_BACKGROUND)
        self.surf.blit(text_surf, (self._x_center(text_surf), self._y_center(text_surf)))
        bar_surf = self._custom_bar()
        self.surf.blit(bar_surf, (uis.PADDING, uis.PADDING))

    def _custom_bar(self):
        """
        Draw progress bar with color map transformation.
        returns: (surface)
        """
        width = int((self.width - 2 * uis.PADDING)
                    * self.percent_complete * 0.01) + 1
        back_arr = pygame.surfarray.array3d(self.surf)
        back_arr = back_arr[1:width, 1:-1]
        back_arr = self._map_color(back_arr)
        return(pygame.surfarray.make_surface(back_arr))

    def _map_color(self, color) -> Optional[int]:
        """
        Map the color to its transformation.
        The coefficients need to be initialized before use.
        args:
        color (np.array)
        """
        if not self.map_is_initialized:
            return
        return (self.coef_m * color + self.coef_b).astype(int)  # type: ignore

    def _init_map_coefficients(self, ai, af, bi, bf):
        """
        Initialize color transformation coefficients.
        The color map will transform ai->af and bi->bf
        args:
        ai :  color a before map
        af :  color a after map
        bi :  color b before map
        bf :  color b after map
        """
        ai = np.array(ai)
        af = np.array(af)
        bi = np.array(bi)
        bf = np.array(bf)
        self.coef_m = (af - bf) / (ai - bi)  # type: ignore
        self.coef_b = af - self.coef_m * ai
        self.map_is_initialized = True
