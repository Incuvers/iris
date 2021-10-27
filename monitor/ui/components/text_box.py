# -*- coding: utf-8 -*-
"""
Textbox
=======
Modified: 2021-07

Dependencies:
-------------
```
import pygame
import textwrap

from .widget import Widget
from monitor.ui.static.settings import UISettings as ui
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import pygame
import textwrap

from .widget import Widget
from monitor.ui.static.settings import UISettings as uis


class TextBox(Widget):
    def __init__(self, width: int, height: int, text: str, fs_min: int, fs_max: int,
                 no_line_breaks=False, color=uis.TEXT_COLOR, justify="left"):
        self.width = width
        self.height = height
        self.text = text
        self.no_line_breaks = no_line_breaks
        self.text_width = self.width  # subtract inner text border padding
        self.font_size_min = fs_min
        self.font_size_max = fs_max
        self.color = color
        self.justify = justify
        self.font_size = 40
        self.font_path = uis.FONT_PATH
        self.font_size = None
        self.update_text(self.text)

    def update_text(self, text):
        self.text = text
        if self.no_line_breaks:
            # a linear increase from min (for 255) to max (for 0)
            self.font_size = int((self.font_size_min - self.font_size_max) /
                                 40. * len(self.text) + self.font_size_max)
        else:
            # a linear increase from min (for 255) to max (for 0)
            self.font_size = int((self.font_size_min - self.font_size_max) /
                                 255. * len(self.text) + self.font_size_max)

    def _get_wrapped_lines(self):
        if self.no_line_breaks:
            lines = [self.text]
        else:
            num_chars_per_line = int(self.text_width / (self.font_size * 0.5))
            lines = textwrap.wrap(self.text, num_chars_per_line)
        return lines

    def redraw(self):
        surf = []
        font = pygame.font.Font(self.font_path, self.font_size)
        if self.no_line_breaks:
            line = self._get_wrapped_lines()[0]
            surf.append(font.render(line, True, self.color, uis.WIDGET_BACKGROUND))
        else:
            for line in self._get_wrapped_lines():
                surf.append(
                    font.render(line, True, self.color, uis.WIDGET_BACKGROUND))
        return surf
