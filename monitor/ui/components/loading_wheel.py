# -*- coding: utf-8 -*-
"""
Loading Wheel
=============
Modified: 2021-07

Module that handles rendering of the loading wheel.

Dependencies:
-------------
```
import pygame
from monitor.ui.static.settings import UISettings as uis
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import pygame
from monitor.ui.static.settings import UISettings as uis


class LoadingWheel:

    def __init__(self, centering: tuple, scaling: tuple, timeout=None, low_res=False):
        if low_res:
            img = pygame.image.load(uis.LOADING_WHEEL_LOW_RES).convert_alpha()
        else:
            img = pygame.image.load(uis.LOADING_WHEEL_HI_RES).convert_alpha()
        self.wheel = img
        self.wheel = pygame.transform.scale(self.wheel, scaling)
        self.rotation = self.wheel
        self.rotation_rect = self.rotation.get_rect()
        self.rotation_rect.center = centering
        if timeout is None:
            self.timeout = timeout
        else:
            self.timeout = timeout * uis.FPS
        self.framecnt = 0
        self.angle = 0
        self.enable = False

    def start(self):
        """
        Set enable and reset frame counter for timeout. The framecnt reset is included here in the
        case that as a current loading wheel condition is true, a new one replaces it and thus
        requires an inherited timeout.
        """
        self.framecnt = 0
        self.enable = True

    def stop(self):
        # unset enable
        self.enable = False

    def update(self):
        """
        Render sequential logic and return surfaces to blit to active widget.

        :return: rotation surface and bg rotation rectangle
        """
        if self.timeout and (self.framecnt == self.timeout):
            self.stop()
        if not self.enable:
            return None
        self.angle += uis.REFRESH_ANGLE
        self.rotation = pygame.transform.rotate(self.wheel, -self.angle)
        x, y = self.rotation_rect.center  # Save its current center.
        self.rotation_rect = self.rotation.get_rect()  # Replace old rect with new rect.
        self.rotation_rect.center = (x, y)  # Put the new rect's center at old center.
        self.framecnt += 1
        return self.rotation, self.rotation_rect
