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
import logging
import time
import signal
import pygame  # type: ignore
from pygame import KEYDOWN, K_RETURN, K_RIGHT, K_LEFT, K_DOWN, K_UP, QUIT, USEREVENT  # type: ignore
from monitor.sys import system
from monitor.ui.menu.service import ServiceMenu
from monitor.ui.views.canvas import Canvas
from monitor.ui.views.loading import Loading
from monitor.ui.menu.main import MainMenu
from monitor.ui.menu.pgm import config_controls
from monitor.ui.components.gauge.o2 import O2Gauge
from monitor.ui.components.gauge.rh import RHGauge
from monitor.ui.components.gauge.co2 import CO2Gauge
from monitor.ui.components.gauge.temp import TempGauge
from monitor.ui.components.device import DeviceWidget
from monitor.ui.components.experiment import ExperimentWidget
from monitor.ui.views.registration import Registration
from monitor.ui.static.settings import UISettings as uis


class UserInterfaceController:
    """
    class is responsible for rendering the graphics and setting/getting the
    values from the sensors
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self.monitor_mode = True
        self.clock = pygame.time.Clock()
        pygame.display.init()
        self._logger.debug(pygame.display.Info())
        self._logger.debug("Display initialized")
        pygame.mouse.set_visible(False)
        self._logger.debug("Mouse visibility removed")
        self.screen = pygame.display.set_mode(
            flags=pygame.NOFRAME | pygame.FULLSCREEN)  # type: ignore
        self._logger.debug("Display mode set")
        # update surface values based on screen resolution
        window_height = self.screen.get_height()
        window_width = self.screen.get_width()
        self._logger.info("Screen height: %s | Screen width: %s", window_height, window_width)
        pygame.font.init()
        # use left/right instead of up/down
        config_controls.MENU_CTRL_UP = config_controls.MENU_CTRL_RIGHT
        config_controls.MENU_CTRL_DOWN = config_controls.MENU_CTRL_LEFT
        # create our canvas
        self.dashboard = Canvas(window_height, window_width)
        self.registration = Canvas(window_height, window_width)
        self.loading = Canvas(window_height, window_width)
        # Add panels to dashboard
        self.dashboard.add_panel(
            widget=DeviceWidget(uis.DEVICE_WIDGET_WIDTH, uis.DEVICE_WIDGET_HEIGHT),
            x_offset=0,
            y_offset=0
        )
        self.dashboard.add_panel(
            widget=ExperimentWidget(uis.EXPERIMENT_WIDGET_WIDTH, uis.EXPERIMENT_WIDGET_HEIGHT),
            x_offset=0,
            y_offset=uis.DEVICE_WIDGET_HEIGHT
        )
        # add gauges to main canvas (they are stored as widgets in the canvas)
        self.dashboard.add_panel(
            widget=TempGauge(uis.GAUGE_WIDGET_WIDTH, uis.GAUGE_WIDGET_HEIGHT),
            x_offset=0,
            y_offset=uis.DEVICE_WIDGET_HEIGHT + uis.EXPERIMENT_WIDGET_HEIGHT
        )
        self.dashboard.add_panel(
            widget=O2Gauge(uis.GAUGE_WIDGET_WIDTH, uis.GAUGE_WIDGET_HEIGHT),
            x_offset=uis.GAUGE_WIDGET_WIDTH,
            y_offset=uis.DEVICE_WIDGET_HEIGHT + uis.EXPERIMENT_WIDGET_HEIGHT
        )
        self.dashboard.add_panel(
            widget=CO2Gauge(uis.GAUGE_WIDGET_WIDTH, uis.GAUGE_WIDGET_HEIGHT),
            x_offset=0,
            y_offset=uis.DEVICE_WIDGET_HEIGHT + uis.EXPERIMENT_WIDGET_HEIGHT + uis.GAUGE_WIDGET_HEIGHT
        )
        self.dashboard.add_panel(
            widget=RHGauge(uis.GAUGE_WIDGET_WIDTH, uis.GAUGE_WIDGET_HEIGHT),
            x_offset=uis.GAUGE_WIDGET_WIDTH,
            y_offset=uis.DEVICE_WIDGET_HEIGHT + uis.EXPERIMENT_WIDGET_HEIGHT + uis.GAUGE_WIDGET_HEIGHT
        )
        self.dashboard_menu = MainMenu(self.screen)
        self.service_menu = ServiceMenu(self.screen)
        # Add registration to registration canvas
        self.registration.add_panel(
            Registration('', window_height, window_width),
            x_offset=0,
            y_offset=0
        )
        # Add splash to splash canvas
        self.loading.add_panel(
            Loading(window_height, window_width),
            x_offset=0,
            y_offset=0
        )
        # enable registration screen as part of the registration pipeline
        self._logger.info("Instantiation successful.")
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(signal):
        print('Signal: {}'.format(signal))
        time.sleep(1)
        system.shutdown()

    def ui_loop(self):
        """
        init function that renders the ui and listens for event
        main event loop for ui events
        """
        # turn off menu
        self.dashboard_menu.main.disable()
        self.service_menu.main.disable()
        while True:
            # Application events
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:  # type: ignore
                    time.sleep(1)
                    system.shutdown()
                elif event.type == USEREVENT:  # type: ignore
                    self.service_menu.main.enable()
                elif event.type == KEYDOWN:  # type: ignore
                    if event.key == K_DOWN:
                        time.sleep(1)
                        system.shutdown()
                    elif event.key in [K_RETURN, K_RIGHT, K_LEFT]:  # type: ignore
                        self.dashboard_menu.main.enable()
            if self.service_menu.main.is_enabled():
                self.service_menu.main.mainloop(events)
            elif self.dashboard_menu.main.is_enabled():
                self.dashboard_menu.main.mainloop(events)
            else:
                self.dashboard.redraw(self.screen)
            self.clock.tick(uis.FPS)
            pygame.display.flip()

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
