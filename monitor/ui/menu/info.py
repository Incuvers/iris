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
import logging
from pathlib import Path

from monitor.sys import system
from monitor.__version__ import __version__
from monitor.ui.menu.pgm.menu import Menu
from monitor.environment.context_manager import ContextManager
from monitor.ui.static.settings import UISettings as uis


class InfoMenu(object):

    user_netplan = '/etc/netplan/60-user-netplan.yaml'
    version_label = 'Version'
    wifi_ip_label = 'WiFi IP'
    wifi_mac_label = 'WiFi MAC'
    hostname_label = 'Hostname'
    eth_ip_label = 'Ethernet IP'
    eth_mac_label = 'Ethernet MAC'

    def __init__(self, main, surface, name, update_func):
        self._logger = logging.getLogger(__name__)
        self.main = main
        self.name = name
        self.update_func = update_func
        self.menu = Menu(
            surface=surface,
            dopause=False,
            font=uis.FONT_PATH,
            menu_alpha=100,
            menu_color=uis.MENU_COLOR,
            menu_color_title=uis.MENU_COLOR_TITLE,
            color_selected=uis.COLOR_SELECTED,
            menu_height=uis.HEIGHT,
            menu_width=uis.WIDTH,
            # If this menu closes (ESC) back to main
            #   onclose=events.PYGAME_MENU_BACK,
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
        hostname = self.get_device_hostname()
        self.hostname_option.label = f"{hostname}"

    def get_device_hostname(self):
        with ContextManager() as context:
            if Path(context.get_env('SNAP_COMMON') + '/hostname.txt').exists() is False:
                self._logger.error("Missing hostname file. Not saved in expected path.")
                return None
            with open(context.get_env('SNAP_COMMON') + '/hostname.txt', 'r') as fp:
                contents = fp.readlines()
                hostname = context.parse_id(contents)
        return hostname

    def _clear_and_return(self):
        self.reset_labels()
        self.menu.reset(1)
