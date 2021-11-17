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

from monitor.sys import system
from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.menu.pgm import events as pge
from monitor.ui.menu.sensors.heater import HeaterMenu
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
            bgfun=self._background_redraw,
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
            title='Service Menu',
            title_offsety=5,
            window_height=uis.HEIGHT,
            window_width=uis.WIDTH,
        )

        self.heater = HeaterMenu(self.main, main_surface)

        # self.temp_benchmark = ConfirmationMenu(
        #     main=self.main,
        #     surface=main_surface,
        #     name='Benchmark Temp.',
        #     callback=system.temp_benchmark,
        #     args=()
        # )

        # self.co2_benchmark = ConfirmationMenu(
        #     main=self.main,
        #     surface=main_surface,
        #     name='Benchmark CO\u2082',
        #     callback=system.co2_benchmark,
        #     args=()
        # )

        # self.o2_benchmark = ConfirmationMenu(
        #     main=self.main,
        #     surface=main_surface,
        #     name='Benchmark O\u2082',
        #     callback=system.o2_benchmark,
        #     args=()
        # )

        # self.full_benchmark = ConfirmationMenu(
        #     main=self.main,
        #     surface=main_surface,
        #     name='Benchmark All',
        #     callback=system.benchmark,
        #     args=()
        # )

        self.network_reset = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Reset Networking',
            callback=system.reset_network,
            args=()
        )

        self.factory_reset = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Factory Reset',
            callback=system.factory_reset,
            args=()
        )

        self.calibrate_dpc_background = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Calibrate Background',
            callback=system.calibrate_dpc,
            args=()
        )

        self.calibrate_co2 = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Calibrate CO\u2082',
            callback=system.calibrate_co2,
            args=()
        )

        self.firmware_flash = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Flash Firmware',
            callback=system.flash_firmware,
            args=()
        )

        self.update_snap = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Update Software',
            callback=system.update_snap,
            args=()
        )

        pygame_exit = ConfirmationMenu(
            main=self.main,
            surface=main_surface,
            name='Shutdown',
            callback=system.shutdown,
            args=()
        )

        self.aux_heater_option = self.main.add_option(
            self.heater.get_title(), self.heater.menu)

        # self.temp_benchmark_option = self.main.add_option(self.temp_benchmark.get_title(), self.temp_benchmark.menu)
        # self.menu_options_to_disable.append(self.temp_benchmark_option)

        # self.co2_benchmark_option = self.main.add_option(self.co2_benchmark.get_title(), self.co2_benchmark.menu)
        # self.menu_options_to_disable.append(self.co2_benchmark_option)

        # self.o2_benchmark_option = self.main.add_option( self.o2_benchmark.get_title(), self.o2_benchmark.menu)
        # self.menu_options_to_disable.append(self.o2_benchmark_option)
        #self.full_benchmark_option = self.main.add_option(self.full_benchmark.get_title(), self.full_benchmark.menu)

        self.menu_options_to_disable.append(
            self.main.add_option(self.network_reset.get_title(), self.network_reset.menu))
        self.menu_options_to_disable.append(
            self.main.add_option(self.factory_reset.get_title(), self.factory_reset.menu))
        self.menu_options_to_disable.append(
            self.main.add_option(self.calibrate_dpc_background.get_title(), self.calibrate_dpc_background.menu))
        self.menu_options_to_disable.append(
            self.main.add_option(self.calibrate_co2.get_title(), self.calibrate_co2.menu))
        self.firmware_flash_option = self.main.add_option(
            self.firmware_flash.get_title(), self.firmware_flash.menu)
        self.menu_options_to_disable.append(self.firmware_flash_option)
        self.update_snap_option = self.main.add_option(
            self.update_snap.get_title(), self.update_snap.menu)
        self.menu_options_to_disable.append(self.update_snap_option)
        # don't make the exit option disabled-able!
        self.main.add_option(pygame_exit.get_title(), pygame_exit.menu)

    def disable_benchmark_options(self, benchmark_test_type):
        for opt in self.menu_options_to_disable:
            opt.set_disable()

    def enable_benchmark_options(self):
        for opt in self.menu_options_to_disable:
            opt.unset_disable()

    def _background_redraw(self):
        self.aux_heater_option.label = self.heater.get_title()
