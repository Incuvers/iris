# coding=utf-8
"""
pygame-menu
https://github.com/ppizarror/pygame-menu

KNOBSELECTOR
KnobSelector class, manage elements and adds entries to menu.

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

import time
import pygame as _pygame
from monitor.ui.menu.pgm import config_controls as _ctrl
from monitor.ui.menu.pgm.widgets.widget import Widget
from monitor.ui.menu.pgm import locals as _locals


class KnobSelector(Widget):
    """
    KnobSelector widget.
    """

    def __init__(self,
                 title,
                 min_val,
                 max_val,
                 start_val,
                 incr=0.1,
                 speed_thresh=0.2,
                 alarm_color=(255, 0, 0),
                 off_on_limit=False,
                 selector_id='',
                 sfmt='{:1f}',
                 onchange=None,
                 onreturn=None,
                 **kwargs
                 ):
        """
        Description of the specific paramaters (see Widget class for generic ones):

        :param title: Title of the selector
        :type title: basestring
        :param elements: Elements of the selector
        :type elements: list
        :param selector_id: ID of the selector
        :type selector_id: basestring
        :param default: Index of default element to display
        :type default: int
        :param onchange: Callback when changing the selector
        :type onchange: function, NoneType
        :param onreturn: Callback when pressing return button
        :type onreturn: function, NoneType
        :param kwargs: Optional keyword-arguments for callbacks
        """
        super(KnobSelector, self).__init__(widget_id=selector_id, onchange=onchange,
                                           onreturn=onreturn, kwargs=kwargs)
        self._elements = []
        self._index = 0
        self._sformat = sfmt
        self._labelsize = 0

        # numerical value of selector
        self._min_val = min_val
        self._max_val = max_val
        self._value = start_val
        self._incr = incr
        self._speed_thresh = speed_thresh
        # behaviour when the selector reaches a limit: show "Off"?
        self._off_on_limit = off_on_limit

        # a list of timestamps for the 5 most recent clicks
        self._clicks = []
        # if value has reached min or max
        self._alarm_color = alarm_color

        # Public attributs
        self.label = title

    def _apply_font(self):
        """
        See upper class doc.
        """
        self._labelsize = self._font.size(self.label)[0]

    def draw(self, surface):
        """
        See upper class doc.
        """
        self._render()
        surface.blit(self._surface, self._rect.topleft)

    def get_value(self):
        """
        Return the current value of the selector.

        :return: Value and index as a float
        :rtype: float
        """
        return self._value

    def set_value(self, value):
        """
        Overriden from parent
        """
        self._value = value

    def get_step(self):
        """
        Return the nonlinear step size. This detects scrolling speed
        (via a moving window buffer of "click" timestamps),
        and adjusts the step size:
        step_value = 0.1 (default);
        step_value = 1.0 (fast);

        :return: Value
        :rtype: float
        """
        step_value = None
        # if click window is no yet fully populated
        if (len(self._clicks) < 5):
            step_value = self._incr
        else:
            delta_time = (self._clicks[-1] - self._clicks[0])
            if delta_time > self._speed_thresh:  # slow, more than 0.9 s for the last 5 clicks
                step_value = self._incr
            else:
                step_value = self._incr * 10
        return step_value

    def decrement(self):
        """
        decrement the value.
        The lowest value is capped at min_val

        :return: None
        """
        # update timestamps
        self._clicks.append(time.time())
        while (len(self._clicks) > 5):
            self._clicks.pop(0)
        self._value -= self.get_step()
        if self._value < self._min_val:
            self._value = self._min_val
        self.change()

    def increment(self):
        """
        increment the value
        The highest value is capped at max_val

        :return: None
        """
        # update timestamps
        self._clicks.append(time.time())
        while (len(self._clicks) > 5):
            self._clicks.pop(0)
        self._value += self.get_step()
        if self._value > self._max_val:
            self._value = self._max_val
        self.change()

    def _render(self):
        """
        See upper class doc.
        """
        if self._off_on_limit:
            if self._value == self._min_val or self._value == self._max_val:
                color = self._alarm_color
                string = "Off"
            else:
                color = self._font_selected_color
                string = self._sformat.format(self.get_value())
        else:
            string = self._sformat.format(self.get_value())
            if self.selected:
                color = self._font_selected_color
            else:
                color = self._font_color
            if self._value == self._min_val or self._value == self._max_val:
                color = self._alarm_color

        self._surface = self.render_string(string, color)

    def set_selection_format(self, s):
        """
        Change the text format.

        :param s: Selection text
        :type s: basestring
        :return: None
        """
        self._sformat = s

    def update(self, events):
        """
        See upper class doc.
        """
        updated = False
        for event in events:
            if event.type == _pygame.KEYDOWN:
                if event.key == _ctrl.MENU_CTRL_LEFT:
                    self.decrement()
                    updated = True
                elif event.key == _ctrl.MENU_CTRL_RIGHT:
                    self.increment()
                    updated = True
                elif event.key == _ctrl.MENU_CTRL_ENTER:
                    self.apply()
                    updated = True

            elif self.joystick_enabled and event.type == _pygame.JOYHATMOTION:
                if event.value == _locals.JOY_LEFT:
                    self.decrement()
                    updated = True
                elif event.value == _locals.JOY_RIGHT:
                    self.increment()
                    updated = True

            elif self.joystick_enabled and event.type == _pygame.JOYAXISMOTION:
                if event.axis == _locals.JOY_AXIS_X and event.value < _locals.JOY_DEADZONE:
                    self.decrement()
                    updated = True
                if event.axis == _locals.JOY_AXIS_X and event.value > -_locals.JOY_DEADZONE:
                    self.increment()
                    updated = True

            elif self.mouse_enabled and event.type == _pygame.MOUSEBUTTONUP:
                if self._rect.collidepoint(*event.pos):
                    # Check if mouse collides left or right as percentage, use only X coordinate
                    mousex, _ = event.pos
                    topleft, _ = self._rect.topleft
                    topright, _ = self._rect.topright
                    dist = mousex - (topleft + self._labelsize)  # Distance from label
                    if dist > 0:  # User clicked options, not label

                        # Position in percentage, if <0.5 user clicked left
                        pos = dist / float(topright - topleft - self._labelsize)
                        if pos <= 0.5:
                            self.decrement()
                        else:
                            self.increment()
                        updated = True

        return updated
