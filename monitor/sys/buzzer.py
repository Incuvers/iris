#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright (C) Incuvers, Inc - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by David Sean
#

# TODO: This should not be a class or Package
import wiringpi

class Buzzer:
    def __init__(self):
        self.pin = 18
        error_code = wiringpi.wiringPiSetupGpio()
        assert error_code == 0, "Could not setup wiringPi, error code {}".format(error_code)
        wiringpi.pinMode(self.pin, wiringpi.GPIO.OUTPUT)

    def __del__(self):
        # turn that god thing off
        wiringpi.digitalWrite(self.pin , 0)

    def beep(self):
        for _ in range(3):
            wiringpi.digitalWrite(self.pin , 1)
            wiringpi.delay(150)
            wiringpi.digitalWrite(self.pin , 0)
            wiringpi.delay(80)

    def off(self):
        wiringpi.digitalWrite(self.pin , 0)



if __name__ == "__main__":
    buzzer=Buzzer()
    buzzer.beep()
    buzzer.off()
