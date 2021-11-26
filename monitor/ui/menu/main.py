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

from monitor.environment.state_manager import StateManager
from monitor.sys import system
from monitor.events.registry import Registry as events
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.ui.menu.info import InfoMenu
from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.menu.pgm import events as pge
from monitor.ui.menu.sensors.o2 import O2Menu
from monitor.ui.menu.sensors.co2 import CO2Menu
from monitor.ui.menu.sensors.fan import FanMenu
from monitor.ui.menu.sensors.temp import TempMenu
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.menu.confirmation import ConfirmationMenu
# from monitor.ui.menu.stream.focus import FocusMenu
# from monitor.ui.menu.stream.exposure.phase import PhaseExposureMenu
# from monitor.ui.menu.stream.exposure.gfp import GFPExposureMenu


class MainMenu:
    """
    This class holds the objects that describe the main menu interface.
    """

    def __init__(self, main_surface):
        # Main menu
        self.main = Menu(
            main_surface,
            color_selected=uis.COLOR_SELECTED,
            bgfun=self._background_redraw,
            loop=False,
            dopause=True,
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
        # sensor menu creation
        self.temp = TempMenu(self.main, main_surface)
        self.CO2 = CO2Menu(self.main, main_surface)
        self.O2 = O2Menu(self.main, main_surface)
        self.fan = FanMenu(self.main, main_surface)
        # set sensor labels in main menu
        self.option_temp = self.main.add_option(self.temp.menu.get_title(), self.temp.menu)
        self.option_co2 = self.main.add_option(self.CO2.menu.get_title(), self.CO2.menu)
        self.option_o2 = self.main.add_option(self.O2.menu.get_title(), self.O2.menu)
        self.option_fan_speed = self.main.add_option(self.fan.menu.get_title(), self.fan.menu)
        self.info = InfoMenu(self.main, main_surface, name='System', update_func=lambda _: None)
        # Imaging
        # self.dpc_exposure = PhaseExposureMenu(
        #     main=self.main,
        #     surface=main_surface,
        #     channel=scope.phase_stream_channel,
        #     min_exposure=0,
        #     max_exposure=100
        # )
        # self.gfp_exposure = GFPExposureMenu(
        #     main=self.main,
        #     surface=main_surface,
        #     channel=scope.gfp_stream_channel,
        #     min_exposure=0,
        #     max_exposure=100
        # )
        # self.image_focus = FocusMenu(
        #     main=self.main,
        #     surface=main_surface,
        #     channel=scope.focus_stream_channel
        # )
        self.update_snap = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Update',
            callback=system.update_snap
        )

        self.service_menu = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Service',
            callback=events.mode_switch.trigger,
            args=(False,)
        )
        # camera settings
        # self.option_focus = self.main.add_option('Focus', self.image_focus.menu)
        # self.option_exposure = self.main.add_option('Phase Exposure', self.dpc_exposure.menu)
        # self.option_gfp_exposure = self.main.add_option('GFP Exposure', self.gfp_exposure.menu)
        # system action settings
        self.main.add_option(self.info.get_title(), self.info.menu)
        self.option_update = self.main.add_option(
            self.update_snap.get_title(), self.update_snap.menu)
        self.main.add_option(self.service_menu.get_title(), self.service_menu.menu)
        self.main.add_option('Home', pge.PYGAME_MENU_CLOSE)
        events.fl_cooldown.register(self.overheat_protection)
        # conditional flag for enabling gfp option in main loop
        self.overheat_protection_active = False

    @tm.threaded(daemon=True)
    def overheat_protection(self):
        self.overheat_protection_active = True
        # time.sleep(FluorescenceHardware.GFP_COOLDOWN)
        self.overheat_protection_active = False

    def _background_redraw(self) -> None:
        """
        When the menu is activated, this method gets called on every menu event-loop
        """
        # determine menu state
        with StateManager() as state:
            experiment = state.experiment
        if not experiment.active:
            self.option_update.disabled = False
            self.option_temp.disabled = False
            self.option_co2.disabled = False
            self.option_o2.disabled = False
            # self.option_exposure.disabled = False
            # if not self.overheat_protection_active:
            #     self.option_gfp_exposure.disabled = False
            # else:
            #     self.option_gfp_exposure.disabled = True
        else:
            # self.option_exposure.disabled = True
            # self.option_gfp_exposure.disabled = True
            self.option_update.disabled = True
            self.option_temp.disabled = True
            self.option_co2.disabled = True
            self.option_o2.disabled = True
        self.option_o2.label = self.O2.get_title()
        self.option_co2.label = self.CO2.get_title()
        self.option_temp.label = self.temp.get_title()
        self.option_fan_speed.label = self.fan.get_title()
        # The currently selected top menu from pygame-menu
        if self.main._top is None:  # NoneType guard
            return
        top_menu = self.main._top._actual
        # phase exposure mode
        # if top_menu == self.dpc_exposure.menu:
        #     if not self.dpc_exposure.active:
        #         self.dpc_exposure.active = True
        #         # start stream asynchronously
        #         self.dpc_exposure.enable_microscope()
        #     self.dpc_exposure.draw_preview()
        # # focus mode
        # elif top_menu == self.image_focus.menu:
        #     if not self.image_focus.active:
        #         self.image_focus.active = True
        #         # start stream asynchronously
        #         self.image_focus.enable_microscope()
        #     self.image_focus.draw_preview()
        # # gfp exposure mode
        # elif top_menu == self.gfp_exposure.menu:
        #     if not self.gfp_exposure.active:
        #         self.gfp_exposure.active = True
        #         # start stream asynchronously
        #         self.gfp_exposure.enable_microscope()
        #     self.gfp_exposure.draw_preview()
        if top_menu == self.info.menu:
            self.info._background_redraw()
        # else:
        #     self.image_focus.active = False
        #     self.gfp_exposure.active = False
        #     self.dpc_exposure.active = False
