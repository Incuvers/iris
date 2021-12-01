# -*- coding: utf-8 -*-
"""
Main Menu
=========
Modified: 2021-07

Dependencies:
-------------
```
import time

from monitor.sys import system
from monitor.models.experiment import Experiment
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.microscope.microscope import Microscope as scope
from monitor.microscope.fluorescence.hardware import FluorescenceHardware
from monitor.ui.menu.info import InfoMenu
from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.menu.pgm import events as pge
from monitor.ui.menu.sensors.o2 import O2Menu
from monitor.ui.menu.sensors.co2 import CO2Menu
from monitor.ui.menu.sensors.fan import FanMenu
from monitor.ui.menu.sensors.temp import TempMenu
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.menu.confirmation import ConfirmationMenu
from monitor.ui.menu.stream.focus import FocusMenu
from monitor.ui.menu.stream.exposure.phase import PhaseExposureMenu
from monitor.ui.menu.stream.exposure.gfp import GFPExposureMenu
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import pygame
from pygame import USEREVENT  # type: ignore
from monitor.events.registry import Registry as events
from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.menu.pgm import events as pge
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.menu.confirmation import ConfirmationMenu


class MainMenu:
    """
    This class holds the objects that describe the main menu interface.
    """

    def __init__(self, main_surface):
        # Main menu
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
            title='Settings',
            title_offsety=5,
            window_height=uis.HEIGHT,
            window_width=uis.WIDTH
        )
        self.main.add_option('Service', self.service)
        self.main.add_option('Home', pge.PYGAME_MENU_CLOSE)

    def service(self):
        # create the event
        event = pygame.event.Event(USEREVENT)  # type: ignore
        pygame.event.post(event)  # add the event to the queue
