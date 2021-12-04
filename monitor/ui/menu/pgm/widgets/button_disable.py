# coding=utf-8
"""
pygame-menu
https://github.com/ppizarror/pygame-menu

BUTTONDISABLE
ButtonDisable class, manage elements and adds entries to menu.

License:
-------------------------------------------------------------------------------
The MIT License (MIT)
Copyright 2017-2019 Pablo Pizarro R. @ppizarror

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
-------------------------------------------------------------------------------
"""

import pygame as _pygame
from monitor.ui.menu.pgm import config_controls as _ctrl
from monitor.ui.menu.pgm.widgets.widget import Widget
from monitor.ui.menu.pgm import locals as _locals


class ButtonDisable(Widget):
    """
    ButtonDisable widget.
    """

    def __init__(self,
                 label,
                 onchange=None,
                 onreturn=None,
                 *args,
                 **kwargs
                 ):
        """
        Description of the specific paramaters (see Widget class for generic ones):

        :param label: Text of the button
        :type label: basestring
        :param onchange: Callback when changing the selector
        :type onchange: function, NoneType
        :param onreturn: Callback when pressing return button
        :type onreturn: function, NoneType
        :param args: Optional arguments for callbacks
        :param kwargs: Optional keyword-arguments for callbacks
        """
        self._is_disabled = False
        self._font_disabled_color = (100, 100, 100)
        self._onreturn_swp = onreturn

        super(ButtonDisable, self).__init__(onchange=onchange, onreturn=onreturn,
                                            args=args, kwargs=kwargs)  # Button has no ID
        # Public attributs
        self.label = label

    def font_disabled_color(self, color):
        self._font_disabled_color = color

    def set_disable(self):
        """ Make this widget disabled
        """
        self._is_disabled = True
        self._on_return = None

    def unset_disable(self):
        """ Make this widget enabled
        """
        self._is_disabled = False
        self._on_return = self._onreturn_swp

    def _apply_font(self):
        """
        See upper class doc.
        """
        pass

    def draw(self, surface):
        """
        See upper class doc.
        """
        self._render()
        surface.blit(self._surface, self._rect.topleft)

    def _render(self):
        """
        See upper class doc.
        """
        if self._is_disabled:
            color = self._font_disabled_color
        elif self.selected:
            color = self._font_selected_color
        else:
            color = self._font_color
        self._surface = self.render_string(self.label, color)

    def update(self, events):
        """
        See upper class doc.
        """
        updated = False
        for event in events:

            if event.type == _pygame.KEYDOWN:
                if event.key == _ctrl.MENU_CTRL_ENTER:
                    self.apply()
                    updated = True

            elif self.joystick_enabled and event.type == _pygame.JOYBUTTONDOWN:
                if event.button == _locals.JOY_BUTTON_SELECT:
                    self.apply()
                    updated = True

            elif self.mouse_enabled and event.type == _pygame.MOUSEBUTTONUP:
                if self._rect.collidepoint(*event.pos):
                    self.apply()
                    updated = True

        return updated
