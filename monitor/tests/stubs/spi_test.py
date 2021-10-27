# import wiringpi
# import time

# ret = wiringpi.wiringPiSetupGpio()
# print("wiringPiSetup status code: ", ret)
# mode = "shiftOut"
# mode = "SPI"

# if mode == "shiftOut":
#     # setup pins
#     MOSI_pin = 10
#     SCLK_pin = 11
#     CE0_pin = 8
#     wiringpi.pinMode(MOSI_pin, 1)
#     wiringpi.pinMode(SCLK_pin, 1)

# elif mode == "SPI":
#     # setup SPI
#     channel = 0  # SPI_CE0  or GPIO 08 or Pin25
#     speed = 500000
#     ret = wiringpi.wiringPiSPISetup(channel, speed)
#     buffer = [0]*32
#     buffer[0] = 255
#     buffer = list(range(1, 33))
#     print("SPIsetup status code: ", ret)
#     print(buffer)


# print("entering while loop in mode", mode)
# while True:
#     time.sleep(1)
#     if mode == "shiftOut":
#         wiringpi.shiftOut(MOSI_pin, SCLK_pin, wiringpi.LSBFIRST, 255)
#         wiringpi.shiftOut(MOSI_pin, SCLK_pin, wiringpi.LSBFIRST, 0)
#     elif mode == "SPI":
#         (retlen, retdata) = wiringpi.wiringPiSPIDataRW(channel, bytes(buffer.copy()))
