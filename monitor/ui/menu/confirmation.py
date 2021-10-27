# -*- coding: utf-8 -*-
"""
Confirmation Menu
=================
Modified: 2021-07

Dependencies:
-------------
```
import logging
from typing import Callable

from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.menu.pgm.events import _PymenuAction
from monitor.ui.static.settings import UISettings as uis
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import logging
from typing import Callable

from monitor.ui.menu.pgm.menu import Menu
from monitor.ui.menu.pgm.events import _PymenuAction
from monitor.ui.static.settings import UISettings as uis


class ConfirmationMenu:

    def __init__(self, main, surface, name: str, callback: Callable, args=None):
        """
        :param main: screen or main view frame
        :param surface: background redraw canvas
        :param name: name of menu i.e temp, o2. co2 for the title
        """
        self._logger = logging.getLogger(__name__)
        self.main = main
        self.name = name
        self.surface = surface
        self.callback = callback
        self.args = args
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
            option_shadow=False,
            rect_width=4,
            title=self.get_title(),
            title_offsety=0,
            window_height=uis.HEIGHT,
            window_width=uis.WIDTH
        )
        self.confirm_option = self.menu.add_option(name, self.exec_and_return)
        self.menu.add_option('Cancel', self.return_to_menu)

    def get_title(self) -> str:
        """
        :return: title name
        """
        return self.name

    def exec_and_return(self):
        """
        Executes callback and returns to previous menu
        """
        # check to ensure the callback is not a pygame menu action event
        if not isinstance(self.callback, _PymenuAction):
            if self.args is None:
                self.callback()
            else:
                self.callback(*self.args)
        self.menu.reset(1)

    def return_to_menu(self):
        """
        Brings the view back to main service menu and executes callback if
        """
        self.menu.reset(1)
