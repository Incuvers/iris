# -*- coding: utf-8 -*-
"""
Widget
======
Date: 2021-07

Dependencies:
-------------
```
import pygame
from monitor.ui.static.settings import UISettings as uisI
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import pygame
from monitor.ui.static.settings import UISettings as uis


class Widget:

    """
    Widget class.
    """

    def __init__(self, width, height):
        """
        init
        """
        self.width = width
        self.height = height
        self.surf = pygame.Surface((self.width, self.height))
        self.font_path = uis.FONT_PATH
        self.redraw()

    def update(self):
        """
        Please
        """
        raise NotImplementedError('Please overide this before calling')

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

    def _x_center(self, surf):
        """
        returns the x-offset to center a surface
        """
        return (self.width - surf.get_width()) / 2

    def _y_center(self, surf: pygame.Surface):  # type: ignore
        """
        returns the y-offset to center a surface
        """
        return (self.height - surf.get_height()) / 2

    def _render_text(self, string, y_offset, font_size, color):
        """
        Renders the string on self.surf
        """
        font = pygame.font.Font(self.font_path, font_size)
        surf = font.render(string, True, color)
        self.surf.blit(surf, (self._x_center(surf), y_offset))

    def get_surface(self):
        return self.surf
