# -*- coding: utf-8 -*-

import time
import logging
import wiringpi  # type: ignore
import numpy as np
from typing import Callable


class RotaryKnob:
    """
    uses this awesome de-bouncing trick: https://www.best-microcontroller-projects.com/rotary-encoder.html
    """

    rot_enc_table = [0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0]

    def __init__(self, push_callback: Callable, rotate_cw_callback: Callable,
                 rotate_ccw_callback: Callable, push_pin=22, clk_pin=17, dt_pin=27):
        """
        init

        Args:
            push_callback (function): callback function for push button click
            rotate_cw_callback (function): callback function for clockwise rotation
            rotate_ccw_callback (function): callback function for counter-clockwise rotation
            push_pin (int): the GPIO pin number for the push button (default pin 22)
            clk_pin (int): the GPIO pin number for the a rotation trigger (default pin 17)
            dt_pin (int): the GPIO pin number for the b rotation trigger (default pin 27)
        """
        self._logger = logging.getLogger(__name__)
        self.push_pin = push_pin  # reset pin on GPIO 10
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.push_state_multiplier = 5

        self.push_callback = push_callback
        self.rotate_cw_callback = rotate_cw_callback
        self.rotate_ccw_callback = rotate_ccw_callback
        self.push_called = time.time()

        error_code = wiringpi.wiringPiSetupGpio()
        if error_code != 0:
            err_message = "Could not setup wiringPi, error code {}".format(error_code)
            self._logger.error(err_message)
            raise OSError(err_message)
        self._logger.info("wiringpi gpio setup successful")
        wiringpi.pinMode(self.push_pin, wiringpi.GPIO.INPUT)
        wiringpi.pinMode(self.clk_pin, wiringpi.GPIO.INPUT)
        wiringpi.pinMode(self.dt_pin, wiringpi.GPIO.INPUT)
        self._logger.info(
            "wiringpi pins %s, %s, and %s set to GPIO input",
            self.push_pin, self.clk_pin, self.dt_pin)

        wiringpi.pullUpDnControl(self.push_pin, wiringpi.GPIO.PUD_UP)
        wiringpi.pullUpDnControl(self.clk_pin, wiringpi.GPIO.PUD_UP)
        wiringpi.pullUpDnControl(self.dt_pin, wiringpi.GPIO.PUD_UP)
        self._logger.info(
            "wiringpi pins %s, %s, and %s set to GPIO pull up down control",
            self.push_pin, self.clk_pin, self.dt_pin)

        self.prev_state = wiringpi.digitalRead(self.clk_pin)
        self.prevNextCode = np.uint8(0)
        self.store = np.uint16(0)
        wiringpi.wiringPiISR(
            self.push_pin, wiringpi.GPIO.INT_EDGE_FALLING, self._push_filter_callback)
        wiringpi.wiringPiISR(
            self.clk_pin, wiringpi.GPIO.INT_EDGE_BOTH, self._rotate_filter_callback)
        wiringpi.wiringPiISR(
            self.dt_pin, wiringpi.GPIO.INT_EDGE_BOTH, self._rotate_filter_callback)
        self._logger.info(
            "wiringpi pins %s, %s, and %s set to GPIO ISRs %s, %s and %s respectively",
            self.push_pin, self.clk_pin, self.dt_pin, wiringpi.GPIO.INT_EDGE_FALLING,
            wiringpi.GPIO.INT_EDGE_BOTH, wiringpi.GPIO.INT_EDGE_BOTH
        )

        self._logger.info("Instantiation successful")

    def _read_rotary(self):
        """
        Reads the rotary instruction(s)
        :return: boolean
        """
        # disabling rotary functions if push knob depressed
        if wiringpi.digitalRead(self.push_pin) == 0:
            self.push_called = time.time()
            self._logger.debug("debouncing from push button")
            return 0
        clk_state = wiringpi.digitalRead(self.clk_pin)
        dt_state = wiringpi.digitalRead(self.dt_pin)
        self._logger.debug("saved digital read states for pins %s and %s",
                           self.clk_pin, self.dt_pin)

        self.prevNextCode <<= np.uint8(2)
        self.prevNextCode &= np.uint8(0x0f)  # just hold to the 4 LSB
        if (clk_state):
            self.prevNextCode |= np.uint8(0x02)
        if (dt_state):
            self.prevNextCode |= np.uint8(0x01)
        self.prevNextCode &= np.uint8(0x0f)  # just hold to the 4 LSB

        # If valid then store as 16 bit data.
        if (self.rot_enc_table[self.prevNextCode]):
            self.store <<= np.uint16(4)
            self.store |= self.prevNextCode
            if (self.store & 0xff) == 0x2b:
                return 1
            if (self.store & 0xff) == 0x17:
                return -1
        return 0

    def _push_filter_callback(self):
        self._logger.debug("push button ISR callback triggered")
        push_state = wiringpi.digitalRead(self.push_pin)
        if time.time() - self.push_called > 0.4:
            if push_state == 0:
                # what happens if I don't come back fast from this function?
                self.push_callback()
        self.push_called = time.time()

    def _rotate_filter_callback(self):
        self._logger.debug("rotary ISR callback triggered")
        direction = self._read_rotary()
        if not direction == 0:
            if direction == 1:
                # what happens if I don't come back fast from this function?
                self.rotate_cw_callback()
            elif direction == -1:
                # what happens if I don't come back fast from this function?
                self.rotate_ccw_callback()
