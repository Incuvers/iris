# -*- coding: utf-8 -*-
"""
Info Menu
=========
Modified: 2021-07

Dependencies:
-------------
```
import logging
from pathlib import Path

from monitor.sys import system
from monitor.__version__ import __version__
from monitor.ui.menu.pgm.menu import Menu
from monitor.environment.context_manager import ContextManager
from monitor.ui.static.settings import UISettings as uis
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import logging
from monitor.sys import system
from monitor.__version__ import __version__
from monitor.ui.menu.pgm.menu import Menu
from monitor.environment.state_manager import StateManager
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.menu.pgm import events as pge
from monitor.events.registry import Registry as events


class InfoMenu:

    user_netplan = '/etc/netplan/60-user-netplan.yaml'
    version_label = 'Version'
    wifi_ip_label = 'WiFi IP'
    wifi_mac_label = 'WiFi MAC'
    hostname_label = 'Hostname'
    eth_ip_label = 'Ethernet IP'
    eth_mac_label = 'Ethernet MAC'
    register_label = 'Register'

    def __init__(self, main, surface, name, update_func):
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.main = main
        self.update_func = update_func
        self.menu = Menu(
            surface=surface,
            mouse_enabled=False,
            bgfun=self._background_redraw,
            font=uis.FONT_PATH,
            menu_alpha=100,
            menu_color=uis.MENU_COLOR,
            menu_color_title=uis.MENU_COLOR_TITLE,
            color_selected=uis.COLOR_SELECTED,
            menu_height=uis.HEIGHT,
            menu_width=uis.WIDTH,
            onclose=pge.PYGAME_MENU_CLOSE,
            option_shadow=False,
            rect_width=4,
            title=self.get_title(),
            title_offsety=0,
            window_height=uis.HEIGHT,
            window_width=uis.WIDTH
        )
        self.version_option = self.menu.add_option(self.version_label, self.refresh_version)
        self.wifi_ip_option = self.menu.add_option(self.wifi_ip_label, self.refresh_wifi_IP)
        self.wifi_mac_option = self.menu.add_option(self.wifi_mac_label, self.refresh_wifi_MAC)
        self.ethernet_ip_option = self.menu.add_option(self.eth_ip_label, self.refresh_ethernet_IP)
        self.ethernet_mac_option = self.menu.add_option(
            self.eth_mac_label, self.refresh_ethernet_MAC)
        self.hostname_option = self.menu.add_option(self.hostname_label, self.refresh_hostname)
        self.register_option = self.menu.add_option(self.register_label, self.refresh_register)
        self.menu.add_option('Back', self._clear_and_return)

    def get_title(self):
        return self.name

    def reset_labels(self):
        self.version_option.label = self.version_label
        self.wifi_ip_option.label = self.wifi_ip_label
        self.wifi_mac_option.label = self.wifi_mac_label
        self.ethernet_ip_option.label = self.eth_ip_label
        self.ethernet_mac_option.label = self.eth_mac_label
        self.hostname_option.label = self.hostname_label
        self.register_option.label = self.register_label

    def refresh_version(self):
        self.version_option.label = __version__

    def refresh_wifi_IP(self):
        ip_address = system.get_ip_address('wlan0')
        self.wifi_ip_option.label = f"{ip_address}"

    def refresh_wifi_MAC(self):
        mac_address = system.get_iface_hardware_address('wlan0')
        self.wifi_mac_option.label = f"{mac_address}"

    def refresh_ethernet_IP(self):
        ip_address = system.get_ip_address('eth0')
        self.ethernet_ip_option.label = f"{ip_address}"

    def refresh_ethernet_MAC(self):
        mac_address = system.get_iface_hardware_address('eth0')
        self.ethernet_mac_option.label = f"{mac_address}"

    def refresh_hostname(self):
        hostname = self._get_device_hostname()
        self.hostname_option.label = f"{hostname}"

    def refresh_register(self):
        self._logger.info("Device not registered, starting registration pipeline.")
        # disable menu first to show registration screen then begin synchrnous pipeline
        self.main.disable()
        events.registration_pipeline.begin()

    def _get_device_hostname(self):
        return os.environ.get('HOSTNAME')

    def _clear_and_return(self):
        self.reset_labels()
        self.menu.reset(1)

    def _background_redraw(self) -> None:
        """
        Dynamic registration option
        """
        with StateManager() as state:
            device = state.device
        if device.registered:
            self.register_option.disabled = True
        else:
            self.register_option.disabled = False
