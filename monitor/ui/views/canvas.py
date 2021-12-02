#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Canvas
======
Modified: 2020-10

This module hosts a list of widget objects for a specific display context. This helps with linking
widgets that need to be displayed in the same window.

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from typing import List
from monitor.ui.components.widget import Widget


class Panel:
    def __init__(self, widget: Widget, x_offset: int, y_offset: int) -> None:
        self.widget = widget
        self.x_offset = x_offset
        self.y_offset = y_offset

    def redraw(self, main_surface):
        self.widget.redraw()
        main_surface.blit(self.widget.get_surface(), (self.x_offset, self.y_offset))


class Canvas:

    def __init__(self, surface_height: int, surface_width: int) -> None:
        self.width = surface_width
        self.height = surface_height
        self.panels: List[Panel] = []

    def add_panel(self, widget: Widget, x_offset: int, y_offset: int):
        self.panels.append(Panel(widget, x_offset, y_offset))

    # def add_gauge_widget(self, widget, loc_idx):
    #     # x,y grid index based on loc_idx = 0,1,2,3
    #     y_offset = self.height - widget.height * 2
    #     i = loc_idx % 2
    #     j = loc_idx // 2
    #     self.widgets.append(widget)
    #     self.coords.append((widget.width * i, y_offset + widget.height * j))

    def redraw(self, main_surface):
        for idx in range(len(self.panels)): self.panels[idx].redraw(main_surface)
