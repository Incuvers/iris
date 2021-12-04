# -*- coding: utf-8 -*-
"""
Device Widget
=============
Modified: 2021-07

Dependencies:
-------------
```
import os
import logging
import pygame
from pathlib import Path

from monitor.ui.components.widget import Widget
from monitor.ui.components.text_box import TextBox
from monitor.models.device import Device
from monitor.models.experiment import Experiment
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.environment.state_manager import StateManager
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import pygame  # type: ignore
import logging
from pathlib import Path

from monitor.ui.components.widget import Widget
from monitor.ui.components.text_box import TextBox
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.state_manager import StateManager
from monitor.ui.components.loading_wheel import LoadingWheel


class Icons:
    # preload all static icons
    def __init__(self) -> None:
        self.syncing = pygame.image.load(uis.STATUS_SYNCING).convert_alpha()
        self.offline = pygame.image.load(uis.STATUS_OFFLINE).convert_alpha()
        self.online = pygame.image.load(uis.STATUS_ONLINE).convert_alpha()
        self.ok = pygame.image.load(uis.STATUS_OK).convert_alpha()
        self.alert = pygame.image.load(uis.STATUS_ALERT).convert_alpha()


class DeviceWidget(Widget):

    def __init__(self, width: int, height: int):
        super().__init__(width, height)
        self._logger = logging.getLogger(__name__)
        self.icons = Icons()
        # register events
        events.cloud_sync.register(self.update_sync_status)
        events.system_status.register(callback=self.update_system_status)
        # stage pipeline events
        events.avatar_pipeline.stage(self.load_avatar_image, 1)
        events.avatar_pipeline.stage(self.update_avatar, 2)
        api_server = ""
        self._logger.debug("Setting development environment text box for identification")
        if os.environ.get('API_BASE_URL') == "https://api.staging.incuvers.com":
            api_server = "STAGING"
            self._logger.debug("Identifying staging server")
        elif os.environ.get('API_BASE_URL') == "https://api.dev.incuvers.com":
            api_server = "DEV"
            self._logger.debug("Identifying dev server")
        elif os.environ.get('API_BASE_URL') == "https://api.prod.incuvers.com":
            api_server = "PROD"
        self.show_status = True
        self._logger.debug("Device Widget width: %s, height: %s", self.width, self.height)
        self.text_box = TextBox(
            width=100,
            height=50,
            text="Welcome to IRIS",
            fs_min=11,
            fs_max=50,
            justify="center",
            no_line_breaks=True
        )
        # idenitfication for dev environment
        self.api_text = TextBox(
            width=100,
            height=50,
            text=api_server,
            fs_min=7,
            fs_max=20,
            justify="center",
            no_line_breaks=True
        )
        # load wheel for working system status
        self.load_icon = LoadingWheel(
            centering=(self.width * 3.58 // 4, self.height * 2.7 // 4),
            scaling=(35, 35)
        )
        self.syncing = False
        avatar = self.load_avatar_image()
        self.update_avatar(avatar)
        self.connection_status_surf = self.icons.offline
        self.system_status_surf = self.icons.ok
        self.update_system_status(uis.STATUS_WORKING)
        self._logger.info("successfully instantiated")

    def load_avatar_image(self) -> pygame.Surface:  # type: ignore
        """
        Load the avatar image from cache

        :raises FileNotFoundError: if the path to the avatar img is not found 
        """
        avatar_path_obj = Path(os.environ.get('COMMON', default='/etc/iris')
                               ).joinpath('device_avatar.png')
        if avatar_path_obj.is_file():
            avatar_path = str(avatar_path_obj)
        else:
            self._logger.warning("No user defined device image found. Using default image")
            avatar_path = uis.AVATAR
        avatar = pygame.image.load(avatar_path)
        self._logger.info("Loaded device image")
        return avatar

    def update_sync_status(self, syncing: bool = False) -> None:
        """
        Enable or disable syncing status icon. If disabled while an experiment is not active.
        The icon falls back to the current device state.

        :param syncing: cloud sync state
        :type syncing: bool
        """
        self.syncing = syncing
        self._logger.debug("Updated syncing status to %s", syncing)

    def update_system_status(self, status: str = None, msg: str = None) -> None:
        """
        Update system status icon.

        :param status: path to status icon
        :type status: str
        :param msg: system status message, defaults to None
        :type msg: str, optional
        """
        # status alert has highest prescedence
        if self.system_status_surf != self.icons.alert:
            if status == "WORKING":
                # start load icon and hide pygame icon
                self.load_icon.start()
                self.show_status = False
            else:
                # load icon and stop loading wheel
                if status == uis.STATUS_ALERT:
                    self.system_status_surf = self.icons.alert
                elif status == uis.STATUS_OK:
                    self.system_status_surf = self.icons.ok
                self.load_icon.stop()
                self.show_status = True

    def update_avatar(self, new_avatar) -> None:
        """
        Update device avatar surf

        :param new_avatar: [description]
        :type new_avatar: pygame.surface
        """
        # TODO: check if size is OK before resizing
        # resize
        target_size = 70
        avatar = pygame.Surface((target_size, target_size))  # type: ignore
        # first step is resize it with the smallest length as avatar_size
        # preserve the smallest dist
        short = new_avatar.get_width()
        if short < new_avatar.get_height():  # in case height is longer
            long = new_avatar.get_height()
            ratio = target_size / short
            new_avatar = pygame.transform.smoothscale(new_avatar,
                                                      (int(ratio * short),
                                                       int(ratio * long)))
            long = int(ratio * long)
            # now crop it as a centered square
            delta = (long - target_size) // 2
            avatar.blit(new_avatar, (0, 0), (0, delta, target_size, long - delta))

        else:  # in case width is longer
            short = new_avatar.get_height()
            long = new_avatar.get_width()
            ratio = target_size / short
            new_avatar = pygame.transform.smoothscale(new_avatar,
                                                      (int(ratio * long),
                                                       int(ratio * short)))
            # now crop it as a centered square
            long = int(ratio * long)
            delta = (long - target_size) // 2
            avatar.blit(new_avatar, (0, 0), (delta, 0, long - delta, target_size))
        # one last tidy-up before, in case of bad rounding
        avatar = pygame.transform.smoothscale(avatar, (80, 80))
        avatar = avatar.convert_alpha()
        mask = pygame.image.load(uis.AVATAR_MASK).convert_alpha()
        avatar.blit(mask, (0, 0), None, pygame.BLEND_RGBA_MULT)  # type:ignore
        self.avatar_surf = avatar

    def redraw(self):
        pygame.draw.rect(
            self.surf,
            uis.INCUVERS_DARK_GREY,
            pygame.Rect(
                0,
                0,
                self.width,
                self.height
            )
        )
        # avatar
        y_offset = self._y_center(self.avatar_surf)
        x_offset = uis.AVATAR_PADDING
        self.surf.blit(self.avatar_surf, (x_offset, y_offset))
        # get system state
        with StateManager() as state:
            experiment = state.experiment
            device = state.device
        if not experiment.active:
            name = device.name
            if self.syncing:
                self.connection_status_surf = self.icons.syncing
            else:
                self.connection_status_surf = self.icons.online if device.mqtt_status else self.icons.offline
        else:
            name = experiment.name
            self.connection_status_surf = self.icons.syncing if device.mqtt_status else self.icons.offline
        self.text_box.update_text(name)
        x_offset += self.avatar_surf.get_width() + uis.AVATAR_PADDING
        text_surf = self.text_box.redraw()
        for surface in text_surf:
            y_offset = self._y_center(surface)
            self.surf.blit(surface, ((self.width - surface.get_width()) / 2, y_offset))
        # for backend stage identification only
        text_surf = self.api_text.redraw()
        for surface in text_surf:
            y_offset = self._y_center(surface)
            self.surf.blit(surface, ((self.width - surface.get_width()) / 2, 10))
        # connection status
        y_offset = 25
        x_offset = self.width - self.connection_status_surf.get_width() - 42
        self.surf.blit(self.connection_status_surf, (x_offset, y_offset))
        # system status
        if self.show_status:
            y_offset = 65
            x_offset = self.width - self.system_status_surf.get_width() - 42
            self.surf.blit(self.system_status_surf, (x_offset, y_offset))
        # render loading wheel
        load_wheel = self.load_icon.update()
        if load_wheel is not None:
            self.surf.blit(load_wheel[0], load_wheel[1])
