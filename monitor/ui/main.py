#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User Interface Controller
=========================
Modified: 2021-07

Dependencies:
-------------
```
import sys
import logging
import pygame

from monitor.sys import kernel
from monitor.events.registry import Registry as events
from monitor.ui.views.canvas import Canvas
from monitor.ui.views.loading import Loading
from monitor.ui.menu.main import MainMenu
from monitor.ui.menu.pgm import config_controls
from monitor.ui.menu.service import ServiceMenu
from monitor.ui.components.gauge.o2 import O2Gauge
from monitor.ui.components.gauge.rh import RHGauge
from monitor.ui.components.gauge.co2 import CO2Gauge
from monitor.ui.components.gauge.temp import TempGauge
from monitor.ui.components.device import DeviceWidget
from monitor.ui.components.experiment import ExperimentWidget
from monitor.ui.views.registration import Registration
from monitor.ui.static.settings import UISettings as uis
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import sys
import time
import logging
import pygame  # type: ignore
from pygame import KEYDOWN, K_RETURN, K_RIGHT, K_LEFT, K_DOWN, K_UP, QUIT, USEREVENT  # type: ignore
from monitor.events.registry import Registry as events
from monitor.ui.views.canvas import Canvas
from monitor.ui.views.loading import Loading
from monitor.ui.menu.main import MainMenu
from monitor.ui.menu.pgm import config_controls
from monitor.ui.menu.service import ServiceMenu
from monitor.models.device import Device
from monitor.ui.components.gauge.o2 import O2Gauge
from monitor.ui.components.gauge.rh import RHGauge
from monitor.ui.components.gauge.co2 import CO2Gauge
from monitor.ui.components.gauge.temp import TempGauge
from monitor.ui.components.device import DeviceWidget
from monitor.ui.components.experiment import ExperimentWidget
from monitor.ui.views.registration import Registration
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.state_manager import PropertyCondition, StateManager


class UserInterfaceController:
    """
    class is responsible for rendering the graphics and setting/getting the
    values from the sensors
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        # show loading screen, use events.system_status.trigger(msg="Hi mom")
        self.load = True
        # don't show registration screen
        self.show_registration = False
        # don't allow user to click-out of loading screen
        self.load_exit = False
        self.monitor_mode = True
        self.screen, self.surface_height, self.surface_width, self.clock = self._init_pygame_menu()
        # create our canvas'
        self.dashboard = Canvas(self.surface_height, self.surface_width)
        self.registration = Canvas(self.surface_height, self.surface_width)
        self.loading = Canvas(self.surface_height, self.surface_width)
        # Add widgets to dashboard canvas
        self.device_info = self._init_device_info_widget()
        # add the info and device widget to the main canvas
        self.dashboard.add_info_widget(self.device_info, y_offset=0)
        self.experiment_info = self._init_experiment_info_widget()
        # add experiment widget to the main canvas
        self.dashboard.add_info_widget(
            self.experiment_info, y_offset=self.surface_height * uis.IW_HEIGHT_RATIO)
        self.dashboard_menu = self._init_menu_values()
        self._service_menu = self._init_service_menu_values()
        # self.guage_widget_yoffset = self.device_info_widget_yoffset + self.surface_height*0.2
        self._gauge_temp, self._gauge_O2, self._gauge_CO2, self._gauge_RH = self._init_gauge_widgets()
        # add gauges to main canvas (they are stored as widgets in the canvas)
        self.dashboard.add_gauge_widget(self._gauge_temp, loc_idx=0)
        self.dashboard.add_gauge_widget(self._gauge_O2, loc_idx=1)
        self.dashboard.add_gauge_widget(self._gauge_CO2, loc_idx=2)
        self.dashboard.add_gauge_widget(self._gauge_RH, loc_idx=3)
        # Add registration to registration canvas
        self.registration.add_info_widget(
            Registration('', self.surface_height, self.surface_width),
            y_offset=0
        )
        # Add splash to splash canvas
        self.loading.add_info_widget(
            Loading(self.surface_height, self.surface_width),
            y_offset=0
        )
        # enable registration screen as part of the registration pipeline
        events.registration_pipeline.stage(self.enable_registration_screen, 0)
        # disable registration screen when registration is successful
        with StateManager() as state:
            state.subscribe_property(
                _type=Device,
                _property=PropertyCondition[Device](
                    trigger=lambda old_device, new_device: not old_device.registered and new_device.registered,
                    callback=self.disable_registration_screen,
                    callback_on_init=False
                )
            )
        events.splash_load.register(self.set_splash_screen)
        events.start_load.register(self.set_load_screen)
        self._logger.info("Instantiation successful.")

    def _init_pygame_menu(self) -> tuple:
        """
        init function responsible for pygame display and config
        :returns tuple: all attributes required for initialization of UIController
        """
        self._logger.info("initializing pygame menu...")
        pygame.display.init()
        self._logger.debug(pygame.display.Info())
        self._logger.debug("Display initialized")
        pygame.mouse.set_visible(False)
        self._logger.debug("Mouse visibility removed")
        screen = pygame.display.set_mode(
            flags=pygame.NOFRAME | pygame.FULLSCREEN | pygame.HWSURFACE)  # type: ignore
        self._logger.debug("Display mode set")
        # update surface values based on screen resolution
        surface_height = screen.get_height()
        surface_width = screen.get_width()
        self._logger.info("Screen height: %s | Screen width: %s", surface_height, surface_width)
        clock = pygame.time.Clock()
        pygame.font.init()
        # use left/right instead of up/down
        config_controls.MENU_CTRL_UP = config_controls.MENU_CTRL_RIGHT
        config_controls.MENU_CTRL_DOWN = config_controls.MENU_CTRL_LEFT
        self._logger.info("pygame menu initialized")
        return screen, surface_height, surface_width, clock

    def _init_device_info_widget(self) -> DeviceWidget:
        """
        The "device-info" widget is the first on top of the Canvas
        """
        self._logger.info("initializing device info widget...")
        # create the Device widget with the default values.
        device_info = DeviceWidget(self.surface_height, self.surface_width)
        self._logger.info("device info widget initialized")
        return device_info

    def _init_experiment_info_widget(self) -> ExperimentWidget:
        """
        The 'experiment-info' widget is the second one, under 'device-info'
        """
        self._logger.info("initializing experiment info widget...")
        experiment_info = ExperimentWidget(self.surface_height, self.surface_width)
        self._logger.info("experiment info widget initialized")
        return experiment_info

    def _init_gauge_widgets(self) -> tuple:
        """Initializes gauge widgets"""
        self._logger.info("initializing gauge info widget...")
        width = int(self.surface_width * uis.GW_WIDTH_RATIO)
        height = int(self.surface_height * uis.GW_HEIGHT_RATIO)
        gauge_temp = TempGauge(width=width, height=height)
        gauge_O2 = O2Gauge(width=width, height=height)
        gauge_CO2 = CO2Gauge(width=width, height=height)
        gauge_RH = RHGauge(width=width, height=height)
        self._logger.info("gauge info widgets initialized")
        return gauge_temp, gauge_O2, gauge_CO2, gauge_RH

    def enable_registration_screen(self):
        """
        This function is the callback for the event which triggers as a result of fetching the
        device info payload
        """
        self.load = False
        self.show_registration = True
        self._logger.info("Updated screen registration status: %s", self.show_registration)

    def set_splash_screen(self, value: bool) -> None:
        self.load = value
        self._logger.info("Set splash screen to %s", self.load)

    def set_load_screen(self, value: bool):
        """
        This function enables/disables the loading screen
        """
        # only set load_exit upon exiting the load screen
        if value:
            self.load = True
        if not value:
            self.load_exit = True
        self._logger.debug("Load screen variable set to %s", self.load_exit)

    async def disable_registration_screen(self, device: Device):
        """
        Update screen based on new device registration status

        :param device: [description]
        :type device: Device
        """
        self.show_registration = False
        self._logger.info("Device registered to lab: %s", device.lab_id)

    def _init_menu_values(self) -> MainMenu:
        """
        loads the menu object with the live sensorframe data and then passes the object to the cloud
        controller class and performs the mirroring logic that always shows the proper value(s)
        when user is selecting or viewing the set point temperature(s) in the menu activated by the
        user
        """
        self._logger.info("initializing main menu...")
        menu = MainMenu(self.screen)
        self._logger.info("main menu initialized")
        return menu

    def _init_service_menu_values(self) -> ServiceMenu:
        """
        loads the menu object with the live sensorframe data and then passes the object to the cloud
        controller class and performs the mirroring logic that always shows the proper value(s) when
        user is selecting or viewing the set point temperature(s) in the menu activated by the user
        """
        self._logger.info("initializing service menu ...")
        service_menu = ServiceMenu(self.screen)
        self._logger.info("service menu initialized")
        return service_menu

    def ui_loop(self):
        """
        main event loop for ui events
        """
        self.dashboard_menu.main.disable()
        self._service_menu.main.disable()
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    self._logger.info("Exiting IRIS application")
                    pygame.display.quit()
                    pygame.font.quit()
                    pygame.quit()  # type: ignore
                    sys.exit(0)
                elif event.type == USEREVENT:
                    self._service_menu.main.enable()
                elif event.type == KEYDOWN:
                    if event.key in [K_RETURN, K_RIGHT, K_LEFT]:  # type: ignore
                        self.dashboard_menu.main.enable()
            if self._service_menu.main.is_enabled():
                self._service_menu.main.mainloop(events)
            elif self.dashboard_menu.main.is_enabled():
                self.dashboard_menu.main.mainloop(events)
            else:
                self.dashboard.redraw(self.screen)
            pygame.display.flip()
            self.clock.tick(uis.FPS)

    def _kret(self) -> None:
        """
        event listener (push event)
        """
        event = pygame.event.Event(KEYDOWN,  # type: ignore
                                   unicode="e",
                                   key=K_RETURN,  # type: ignore
                                   mod=pygame.locals.KMOD_NONE)  # type: ignore
        pygame.event.post(event)  # add the event to the queue

    def _kright(self) -> None:
        """
        event listener (clock-wise rotation event)
        """
        event = pygame.event.Event(KEYDOWN,  # type: ignore
                                   unicode="r",
                                   key=K_RIGHT,  # type: ignore
                                   mod=pygame.locals.KMOD_NONE)   # type: ignore
        pygame.event.post(event)  # add the event to the queue

    def _kleft(self) -> None:
        """
        event listener (counter-clock-wise rotation event)
        """
        # create the event
        event = pygame.event.Event(KEYDOWN,  # type: ignore
                                   unicode="l",
                                   key=K_LEFT,  # type: ignore
                                   mod=pygame.locals.KMOD_NONE)  # type: ignore
        pygame.event.post(event)  # add the event to the queue

    def _kdown(self) -> None:
        """
        event listener (counter-clock-wise rotation event)
        """
        # create the event
        event = pygame.event.Event(KEYDOWN,  # type: ignore
                                   unicode="d",
                                   key=K_DOWN,  # type: ignore
                                   mod=pygame.locals.KMOD_NONE)  # type: ignore
        pygame.event.post(event)  # add the event to the queue

    def _kup(self) -> None:
        """
        event listener (counter-clock-wise rotation event)
        """
        # create the event
        event = pygame.event.Event(KEYDOWN,  # type: ignore
                                   unicode="u",
                                   key=K_UP,  # type: ignore
                                   mod=pygame.locals.KMOD_NONE)  # type: ignore
        pygame.event.post(event)  # add the event to the queue
