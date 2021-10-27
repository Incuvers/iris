import sys
import time
import wiringpi  # type: ignore
from .fbshow import FrameBufShow

error_code = wiringpi.wiringPiSetupGpio()
push_pin = 22
wiringpi.pinMode(push_pin, wiringpi.GPIO.INPUT)
wiringpi.pullUpDnControl(push_pin, wiringpi.GPIO.PUD_UP)

try:
    text = sys.argv[1]
except IndexError:
    text = None
fb = FrameBufShow('/dev/fb0')
fb.show(text=text)

push_state = 1
timeout = 1
time_start = time.time()

# poll until press or timeout
while push_state and (time.time() - time_start) < timeout:
    push_state = wiringpi.digitalRead(push_pin)

# need to print the state
print(push_state)
