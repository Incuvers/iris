# import wiringpi
# import time


# # rotary encoder
# def test_rotaryencoder():
#     push_pin = 22
#     a_pin = 17
#     b_pin = 27
#     wiringpi.pullUpDnControl(push_pin, wiringpi.GPIO.PUD_UP)
#     wiringpi.pullUpDnControl(a_pin, wiringpi.GPIO.PUD_UP)
#     wiringpi.pullUpDnControl(b_pin, wiringpi.GPIO.PUD_UP)
#     wiringpi.digitalRead(push_pin)
#     wiringpi.digitalRead(a_pin)
#     wiringpi.digitalRead(b_pin)

# def test_fluorescence():
#     # fluorescence
#     trigger_pin = 21  # BCM_21
#     on_when_high = True
#     wiringpi.pinMode(trigger_pin, wiringpi.OUTPUT)

# def test_automatrix():
#     # automatrix
#     trigger_pin = 25  # BCM_25
#     on_when_high = False
#     wiringpi.digitalWrite(trigger_pin, on_when_high)

#     # automatrix
#     channel = 0
#     speed = 500000
#     wiringpi.wiringPiSPISetup(channel, speed)


# ret = wiringpi.wiringPiSetupGpio()
# print("wiringPiSetup status code: ", ret)

# test_rotaryencoder()
# test_fluorescence()
# test_automatrix()
