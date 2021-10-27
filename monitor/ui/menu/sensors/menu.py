# -*- coding: utf-8 -*-
"""
Sensors Menu
============

Dependancies
------------
```
from .incuvers_settings_ui import IncuversSettingsUI
from .pygameMenu import Menu
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
from typing import Generic, TypeVar, Union
from monitor.models.icb import ICB
from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.static.settings import UISettings as uis

_T = TypeVar('_T', bound=Union[int, float])


class SensorMenu(Generic[_T]):

    def __init__(self, main, surface, name: str, min_val: _T, max_val: _T, default: _T, sfmt: str,
                 incr: _T, modal: bool):
        self.main = main
        self.value = default
        self.candidate_value = default
        self.name = name
        self.modal = modal
        self.min_val = min_val - 0.1 if self.modal else min_val
        self.max_val = max_val + 0.1 if self.modal else max_val
        self.incr = incr
        self.menu = Menu(
            surface=surface,
            dopause=True,
            bgfun=self.bgfun,
            font=uis.FONT_PATH,
            menu_alpha=100,
            menu_color=uis.MENU_COLOR,
            menu_color_title=uis.MENU_COLOR_TITLE,
            color_selected=uis.COLOR_SELECTED,
            menu_height=uis.HEIGHT,
            menu_width=uis.WIDTH,
            option_shadow=False,
            rect_width=4,
            title=name,
            title_offsety=0,
            window_height=uis.HEIGHT,
            window_width=uis.WIDTH
        )
        self.selector = self.menu.add_knob_selector(
            title="Set",
            min_val=self.min_val,
            max_val=self.max_val,
            start_val=default,
            incr=self.incr,
            speed_thresh=0.3,
            alarm_color=(255, 0, 0),
            off_on_limit=self.modal,
            selector_id='',
            sfmt=sfmt,
            onchange=None,
            onreturn=self.try_value,
            write_on_console=False
        )
        self.menu.add_option('OK', self.confirm_value)
        self.menu.add_option('Cancel', self.cancel_value)

    async def update(self, _: ICB) -> None:
        raise NotImplementedError

    def get_title(self) -> str:
        raise NotImplementedError

    def cancel_value(self) -> None:
        raise NotImplementedError

    def confirm_value(self) -> None:
        raise NotImplementedError

    def try_value(self, value: _T, c=None, **kwargs):
        """
        function performs a try action that attempts to set the candidate value or user chosen value
        """
        self.candidate_value = value
        self.main._select(self.main._actual._index + 1)

    def bgfun(self) -> None:
        """ dummy background function
        This does nothing. Doesn't event seem to be called.
        But we need it for dopause=True.
        And we need dopause=True for the main menu's background 
        function to continue to be called.
        """
        pass
