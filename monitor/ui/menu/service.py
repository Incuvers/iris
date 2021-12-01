#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Service Menu
============
Modified: 2021-05

Dependancies
------------
```
import logging

from monitor.sys import system
from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.menu.pgm import events as pge
from monitor.ui.menu.sensors.heater import HeaterMenu
from monitor.ui.menu.confirmation import ConfirmationMenu
from monitor.ui.static.settings import UISettings as ui
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import pygame
from pygame import QUIT
from monitor.sys import system
from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.menu.pgm import events as pge
from monitor.ui.menu.confirmation import ConfirmationMenu
from monitor.ui.static.settings import UISettings as uis


class ServiceMenu:

    def __init__(self, main_surface):
        """
        :param main_surface: screen or main view frame
        :param bgfun: background redraw canvas
        """
        self._logger = logging.getLogger(__name__)
        self.main_surface = main_surface
        self.test_in_progress = False
        # keep a list of options to quickly disable them all
        self.menu_options_to_disable = []
        self.main = Menu(
            main_surface,
            color_selected=uis.COLOR_SELECTED,
            loop=False,
            dopause=False,
            font=uis.FONT_PATH,
            mouse_enabled=False,
            menu_color=uis.MENU_COLOR,
            menu_color_title=uis.MENU_COLOR_TITLE,
            menu_height=uis.HEIGHT,
            menu_width=uis.WIDTH,
            menu_alpha=100,
            onclose=pge.PYGAME_MENU_CLOSE,
            option_shadow=False,
            rect_width=4,
            title='Service Menu',
            title_offsety=5,
            window_height=uis.HEIGHT,
            window_width=uis.WIDTH,
        )
        system_shutdown = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Shutdown',
            callback=self.quit,
            args=()
        )
        self.main.add_option(system_shutdown.get_title(), system_shutdown.menu)
        self.main.add_option('Return', pge.PYGAME_MENU_CLOSE)

    def quit(self):
        # create the event
        event = pygame.event.Event(QUIT)  # type: ignore
        pygame.event.post(event)  # add the event to the queue
