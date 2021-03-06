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

class Canvas:

    def __init__(self, surface_height, surface_width):
        """
        init
        """
        self.width = surface_width
        self.height = surface_height
        self.widgets = []
        self.coords = []

    def add_info_widget(self, widget, y_offset):
        self.widgets.append(widget)
        self.coords.append((0, y_offset))

    def add_gauge_widget(self, widget, loc_idx):
        # x,y grid index based on loc_idx = 0,1,2,3
        y_offset = self.height - widget.height*2
        i = loc_idx % 2
        j = loc_idx // 2
        self.widgets.append(widget)
        self.coords.append((widget.width*i, y_offset+widget.height*j))

    def redraw(self, main_surface):
        for idx in range(len(self.widgets)):
            self.widgets[idx].redraw()
            main_surface.blit(self.widgets[idx].get_surface(), self.coords[idx])
