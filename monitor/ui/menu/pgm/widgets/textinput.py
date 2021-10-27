# coding=utf-8
"""
pygame-menu
https://github.com/ppizarror/pygame-menu

TEXT INPUT
Text input class, this widget lets user to write text.

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
from monitor.ui.menu.pgm import locals as _locals
from monitor.ui.menu.pgm.widgets.widget import Widget


class TextInput(Widget):
    """
    Text input widget.
    """

    def __init__(self,
                 label='',
                 default='',
                 textinput_id='',
                 input_type=_locals.PYGAME_INPUT_TEXT,
                 cursor_color=(0, 0, 1),
                 maxchar=0,
                 maxwidth=0,
                 onchange=None,
                 onreturn=None,
                 repeat_keys_initial_ms=400,
                 repeat_keys_interval_ms=35,
                 repeat_mouse_interval_ms=200,
                 text_ellipsis='...',
                 **kwargs
                 ):
        """
        Description of the specific paramaters (see Widget class for generic ones):

        :param label: Input label text
        :type label: basestring
        :param default: Initial text to be displayed
        :type default: basestring
        :param textinput_id: Id of the text input
        :type textinput_id: basestring
        :param input_type: Type of data
        :type input_type: basestring
        :param cursor_color: Color of cursor
        :type cursor_color: tuple
        :param maxchar: Maximum length of input
        :type maxchar: int
        :param maxwidth: Maximum size of the text to be displayed (overflow)
        :type maxwidth: int
        :param onchange: Callback when changing the selector
        :type onchange: function, NoneType
        :param onreturn: Callback when pressing return button
        :type onreturn: function, NoneType
        :param repeat_keys_initial_ms: Time in ms before keys are repeated when held
        :type repeat_keys_initial_ms: float, int
        :param repeat_keys_interval_ms: Interval between key press repetition when held
        :type repeat_keys_interval_ms: float, int
        :param repeat_mouse_interval_ms: Interval between mouse events when held
        :type repeat_mouse_interval_ms: float, int
        :param text_ellipsis: Ellipsis text when overflow occurs
        :type text_ellipsis: basestring
        :param kwargs: Optional keyword-arguments for callbacks
        """
        super(TextInput, self).__init__(widget_id=textinput_id, onchange=onchange,
                                        onreturn=onreturn, kwargs=kwargs)
        if maxchar < 0:
            raise Exception('maxchar must be equal or greater than zero')
        if maxwidth < 0:
            raise Exception('maxwidth must be equal or greater than zero')

        self._input_string = str(default)  # Inputted text
        self._ignore_keys = (_ctrl.MENU_CTRL_UP, _ctrl.MENU_CTRL_DOWN,
                             _pygame.K_LCTRL, _pygame.K_RCTRL,
                             _pygame.K_LSHIFT, _pygame.K_RSHIFT,
                             _pygame.K_NUMLOCK, _pygame.K_CAPSLOCK,
                             _pygame.K_TAB, _pygame.K_RETURN, _pygame.K_ESCAPE)

        # Vars to make keydowns repeat after user pressed a key for some time:
        self._keyrepeat_counters = {}  # {event.key: (counter_int, event.unicode)} (look for "***")
        self._keyrepeat_interval_ms = repeat_keys_interval_ms
        self._keyrepeat_initial_interval_ms = repeat_keys_initial_ms

        # Mouse handling
        self._keyrepeat_mouse_ms = 0
        self._keyrepeat_mouse_interval_ms = repeat_mouse_interval_ms
        self._mouse_is_pressed = False

        # Render box (overflow)
        self._ellipsis = text_ellipsis
        self._ellipsis_size = 0
        self._renderbox = [0, 0, 0]  # Left/Right/Inner

        # Things cursor:
        self._clock = _pygame.time.Clock()
        self._cursor_color = cursor_color
        self._cursor_ms_counter = 0
        self._cursor_position = len(self._input_string)  # Inside text
        self._cursor_render = True  # If true cursor must be rendered
        self._cursor_surface = None
        self._cursor_surface_pos = [0, 0]  # Position (x,y) of surface
        self._cursor_switch_ms = 500  # /|\
        self._cursor_visible = False  # Switches every self._cursor_switch_ms ms

        # Public attributs
        self.label = label
        self.maxchar = maxchar
        self.maxwidth = maxwidth

        # Other
        self._input_type = input_type
        self._label_size = 0

    def _apply_font(self):
        """
        See upper class doc.
        """
        self._ellipsis_size = self._font.size(self._ellipsis)[0]
        self._label_size = self._font.size(self.label)[0]

    def clear(self):
        """
        Clear the current text.

        :return: None
        """
        self._input_string = ''
        self._cursor_position = 0

    def get_value(self):
        """
        See upper class doc.
        """
        value = ''
        if self._input_type == _locals.PYGAME_INPUT_TEXT:
            value = self._input_string
        elif self._input_type == _locals.PYGAME_INPUT_FLOAT:
            try:
                value = float(self._input_string)
            except ValueError:
                value = 0
        elif self._input_type == _locals.PYGAME_INPUT_INT:
            try:
                value = int(self._input_string)
            except ValueError:
                value = 0
        return value

    def draw(self, surface):
        """
        See upper class doc.
        """
        self._clock.tick()
        self._render()

        # Draw string
        surface.blit(self._surface, (self._rect.x, self._rect.y))

        # Draw cursor
        if (self._cursor_visible and self.selected) or self._mouse_is_pressed:
            surface.blit(self._cursor_surface, (self._rect.x + self._cursor_surface_pos[0],
                                                self._rect.y + self._cursor_surface_pos[1]))

    def _render(self):
        """
        See upper class doc.
        """
        string = self.label + self._get_input_string()
        if self.selected:
            color = self._font_selected_color
        else:
            color = self._font_color
        self._surface = self.render_string(string, color)
        self._render_cursor()

    def _render_cursor(self):
        """
        Cursor is rendered and stored.

        :return: None
        """
        # Cursor should not be rendered
        if not self._cursor_render:
            return

        # Cursor surface does not exist
        if self._cursor_surface is None:
            if self._rect.height == 0:  # If menu has not been initialized this error can occur
                return
            self._cursor_surface = _pygame.Surface(
                (int(self._font_size / 20 + 1), self._rect.height - 2))
            self._cursor_surface.fill(self._cursor_color)

        # Calculate x position If no limit is provided
        if self.maxwidth == 0 or len(self._input_string) <= self.maxwidth:
            cursor_x_pos = 2 + self._font.size(
                self.label + self._input_string[:self._cursor_position])[0]
        else:  # Calculate position depending on renderbox
            sstring = self._input_string
            sstring = sstring[self._renderbox[0]:(self._renderbox[0] + self._renderbox[2])]
            cursor_x_pos = 2 + self._font.size(self.label + sstring)[0]

            # Add ellipsis
            delta = self._ellipsis_size
            if self._renderbox[0] != 0 and \
                    self._renderbox[1] != len(self._input_string):  # If Left+Right ellipsis
                delta *= 1
            elif self._renderbox[1] != len(self._input_string):  # Right ellipsis
                delta *= 0
            elif self._renderbox[0] != 0:  # Left ellipsis
                delta *= 1
            else:
                delta *= 0
            cursor_x_pos += delta
        if self._cursor_position > 0 or (self.label and self._cursor_position == 0):
            # Without this, the cursor is invisible when self._cursor_position > 0:
            cursor_x_pos -= self._cursor_surface.get_width()

        # Calculate y position
        cursor_y_pos = 1

        # Store position
        self._cursor_surface_pos[0] = cursor_x_pos
        self._cursor_surface_pos[1] = cursor_y_pos
        self._cursor_render = False

    def _get_input_string(self):
        """
        Return input string, apply overflow if enabled.

        :return: String
        """
        if self.maxwidth != 0 and len(self._input_string) > self.maxwidth:
            text = self._input_string[self._renderbox[0]:self._renderbox[1]]
            if self._renderbox[1] != len(self._input_string):  # Right ellipsis
                text += self._ellipsis
            if self._renderbox[0] != 0:  # Left ellipsis
                text = self._ellipsis + text
            return text
        else:
            return self._input_string

    def _update_renderbox(self, left=0, right=0, addition=False, end=False, start=False):
        """
        Update renderbox position.

        :param left: Left update
        :param right: Right update
        :param addition: Update is text addition/deletion
        :param end: Move cursor to end
        :param start: Move cursor to start
        :type left: int
        :type right: int
        :type addition: bool
        :type end: bool
        :type start: bool
        :return: None
        """
        self._cursor_render = True
        if self.maxwidth == 0:
            return
        ls = len(self._input_string)

        # Move cursor to end
        if end:
            self._renderbox[0] = max(0, ls - self.maxwidth)
            self._renderbox[1] = ls
            self._renderbox[2] = min(ls, self.maxwidth)
            return

        # Move cursor to start
        if start:
            self._renderbox[0] = 0
            self._renderbox[1] = min(ls, self.maxwidth)
            self._renderbox[2] = 0
            return

        # Check limits
        if left < 0 and ls == 0:
            return

        # If no overflow
        if ls <= self.maxwidth:
            if right < 0 and self._renderbox[2] == ls:  # If del at the end of string
                return
            self._renderbox[0] = 0  # To catch unexpected errors
            if addition:  # left/right are ignored
                if left < 0:
                    self._renderbox[1] += left
                self._renderbox[1] += right
                if right < 0:
                    self._renderbox[2] -= right

            # If text is typed increase inner position
            self._renderbox[2] += left
            self._renderbox[2] += right
        else:
            if addition:  # If text is added
                if right < 0 and self._renderbox[2] == self.maxwidth:  # If del at the end of string
                    return
                if left < 0 and self._renderbox[2] == 0:  # If backspace at begining of string
                    return

                # If user deletes something and it is in the end
                if right < 0:  # del
                    if self._renderbox[0] != 0:
                        if (self._renderbox[1] - 1) == ls:  # At the end
                            self._renderbox[2] -= right

                # If the user writes, move renderbox
                if right > 0:
                    if self._renderbox[2] == self.maxwidth:  # If cursor is at the end push box
                        self._renderbox[0] += right
                        self._renderbox[1] += right
                    self._renderbox[2] += right

                if left < 0:
                    if self._renderbox[0] == 0:
                        self._renderbox[2] += left
                    self._renderbox[0] += left
                    self._renderbox[1] += left

            if not addition:  # Move inner (left/right)
                self._renderbox[2] += right
                self._renderbox[2] += left

                # If user pushes after limit the renderbox moves
                if self._renderbox[2] < 0:
                    self._renderbox[0] += left
                    self._renderbox[1] += left
                if self._renderbox[2] > self.maxwidth:
                    self._renderbox[0] += right
                    self._renderbox[1] += right

            # Apply string limits
            self._renderbox[1] = max(self.maxwidth, min(self._renderbox[1], ls))
            self._renderbox[0] = self._renderbox[1] - self.maxwidth

        # Apply limits
        self._renderbox[0] = max(0, self._renderbox[0])
        self._renderbox[1] = max(0, self._renderbox[1])
        self._renderbox[2] = max(0, min(self._renderbox[2], min(self.maxwidth, ls)))

    def _update_cursor_mouse(self, mousex):
        """
        Updates cursor position after mouse click in text.

        :param mousex: Mouse distance relative to surface
        :type mousex: int
        :return: None
        """
        string = self._get_input_string()
        if string == '':  # If string is empty cursor is not updated
            return

        # Calculate size of each character
        string_size = []
        string_total_size = 0
        for i in range(len(string)):
            cs = self._font.size(string[i])[0]  # Char size
            string_size.append(cs)
            string_total_size += cs

        # Find the accumulated char size that gives the position of cursor
        size_sum = 0
        cursor_pos = len(string)
        for i in range(len(string)):
            size_sum += string_size[i] / 2
            if self._label_size + size_sum >= mousex:
                cursor_pos = i
                break
            size_sum += string_size[i] / 2

        # If text have ellipsis
        if self.maxwidth != 0 and len(self._input_string) > self.maxwidth:
            if self._renderbox[0] != 0:  # Left ellipsis
                cursor_pos -= 3

            # Check if user clicked on ellipsis
            if cursor_pos < 0 or cursor_pos > self.maxwidth:
                if cursor_pos < 0:
                    self._renderbox[2] = 0
                    self._move_cursor_left()
                if cursor_pos > self.maxwidth:
                    self._renderbox[2] = self.maxwidth
                    self._move_cursor_right()
                return

            # User clicked on text, update cursor
            cursor_pos = max(0, min(self.maxwidth, cursor_pos))
            self._cursor_position = self._renderbox[0] + cursor_pos
            self._renderbox[2] = cursor_pos

        # Text does not have ellipsis, infered position is correct
        else:
            self._cursor_position = cursor_pos
        self._cursor_render = True

    def _check_mouse_collide_input(self, pos):
        """
        Check mouse collision, if true update cursor.

        :param pos: Position
        :type pos: tuple
        :return: None
        """
        if self._rect.collidepoint(*pos):
            # Check if mouse collides left or right as percentage, use only X coordinate
            mousex, _ = pos
            topleft, _ = self._rect.topleft
            self._update_cursor_mouse(mousex - topleft)
            return True  # Prevents double click

    def set_value(self, text):
        """
        See upper class doc.
        """
        self._input_string = text

    def _check_input_size(self):
        """
        Check input size.

        :return: True if the input must be limited
        :rtype: bool
        """
        if self.maxchar == 0:
            return False
        return self.maxchar < len(self._input_string)

    def _check_input_type(self, string):
        """
        Check if input type is valid.

        :param string: String to validate
        :type string: basestring
        :return: True if the input type is valid
        :rtype: bool
        """
        if self._input_type == _locals.PYGAME_INPUT_TEXT:
            return True

        conv = None
        if self._input_type == _locals.PYGAME_INPUT_FLOAT:
            conv = int
        elif self._input_type == _locals.PYGAME_INPUT_INT:
            conv = float

        if string == '-':
            return True

        if conv is None:
            return False

        try:
            conv(string)
            return True
        except ValueError:
            return False

    def _move_cursor_left(self):
        """
        Move cursor to left position.

        :return: None
        """
        # Subtract one from cursor_pos, but do not go below zero:
        self._cursor_position = max(self._cursor_position - 1, 0)
        self._update_renderbox(left=-1)

    def _move_cursor_right(self):
        """
        Move cursor to right position.

        :return: None
        """
        # Add one to cursor_pos, but do not exceed len(input_string)
        self._cursor_position = min(self._cursor_position + 1, len(self._input_string))
        self._update_renderbox(right=1)

    def update(self, events):
        """
        See upper class doc.
        """
        updated = False
        for event in events:
            if event.type == _pygame.KEYDOWN:
                self._cursor_visible = True  # So the user sees where he writes

                # If none exist, create counter for that key:
                if event.key not in self._keyrepeat_counters and event.key not in self._ignore_keys:
                    self._keyrepeat_counters[event.key] = [0, event.unicode]

                if event.key == _pygame.K_BACKSPACE:
                    self._input_string = (
                        self._input_string[:max(self._cursor_position - 1, 0)]
                        + self._input_string[self._cursor_position:]
                    )
                    self._update_renderbox(left=-1, addition=True)
                    self.change()
                    updated = True

                    # Subtract one from cursor_pos, but do not go below zero:
                    self._cursor_position = max(self._cursor_position - 1, 0)

                elif event.key == _pygame.K_DELETE:
                    self._input_string = (
                        self._input_string[:self._cursor_position]
                        + self._input_string[self._cursor_position + 1:]
                    )
                    self._update_renderbox(right=-1, addition=True)
                    self.change()
                    updated = True

                elif event.key == _pygame.K_RIGHT:
                    self._move_cursor_right()
                    updated = True

                elif event.key == _pygame.K_LEFT:
                    self._move_cursor_left()
                    updated = True

                elif event.key == _pygame.K_END:
                    self._cursor_position = len(self._input_string)
                    self._update_renderbox(end=True)
                    updated = True

                elif event.key == _pygame.K_HOME:
                    self._cursor_position = 0
                    self._update_renderbox(start=True)
                    updated = True

                elif event.key == _ctrl.MENU_CTRL_ENTER:
                    self.apply()
                    updated = True

                elif event.key not in self._ignore_keys:
                    # Check input has not exceeded the limit
                    if self._check_input_size():
                        break

                    # If no special key is pressed, add unicode of key to input_string
                    new_string = (
                        self._input_string[:self._cursor_position]
                        + event.unicode
                        + self._input_string[self._cursor_position:]
                    )

                    # If data is valid
                    if self._check_input_type(new_string):
                        self._input_string = new_string

                        lkey = len(event.unicode)
                        if lkey > 0:
                            self._cursor_position += lkey  # Some are empty, e.g. K_UP
                            self._update_renderbox(right=1, addition=True)
                            self.change()
                            updated = True

            elif event.type == _pygame.KEYUP:
                # KEYUP doesn't include event.unicode, this dict is stored in such a weird way
                if event.key in self._keyrepeat_counters:
                    del self._keyrepeat_counters[event.key]

            elif self.mouse_enabled and event.type == _pygame.MOUSEBUTTONUP:
                self._check_mouse_collide_input(event.pos)

        # Get time clock
        time_clock = self._clock.get_time()
        self._keyrepeat_mouse_ms += time_clock

        # Check mouse pressed
        mouse_left, mouse_middle, mouse_right = _pygame.mouse.get_pressed()
        self._mouse_is_pressed = mouse_left or mouse_right or mouse_middle

        if self._keyrepeat_mouse_ms > self._keyrepeat_mouse_interval_ms:
            self._keyrepeat_mouse_ms = 0
            if mouse_left:
                self._check_mouse_collide_input(_pygame.mouse.get_pos())

        # Update key counters:
        for key in self._keyrepeat_counters:
            self._keyrepeat_counters[key][0] += time_clock  # Update clock

            # Generate new key events if enough time has passed:
            if self._keyrepeat_counters[key][0] >= self._keyrepeat_initial_interval_ms:
                self._keyrepeat_counters[key][0] = self._keyrepeat_initial_interval_ms - \
                    self._keyrepeat_interval_ms

                event_key, event_unicode = key, self._keyrepeat_counters[key][1]
                # noinspection PyArgumentList
                _pygame.event.post(_pygame.event.Event(_pygame.KEYDOWN,
                                                       key=event_key,
                                                       unicode=event_unicode)
                                   )

        # Update self._cursor_visible
        self._cursor_ms_counter += time_clock
        if self._cursor_ms_counter >= self._cursor_switch_ms:
            self._cursor_ms_counter %= self._cursor_switch_ms
            self._cursor_visible = not self._cursor_visible

        return updated
