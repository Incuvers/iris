#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright (C) Incuvers, Inc - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by David Sean
#
# import numpy as np
# import time
# from monitor.microscope.pinwheel import Pinwheel
# from monitor.display import Display


# if __name__ == "__main__":

#     cam = Pinwheel()
#     #light_pat = cam.get_pattern_as_array(0)

#     display = Display()
#     display.countdown()

#     imgs = cam.take_snaphot()
#     for img in imgs:
#         display.show(img)
#         time.sleep(.2)
#     for img in imgs:
#         print("mean: {}".format(np.mean(img)))
#         print("max: {}".format(np.max(img)))
#         print("min: {}".format(np.min(img)))
#         display.show(img)
#         time.sleep(1)
#     #while True:
#     #    for img in imgs:
#     #        display.show(img)
#     #        time.sleep(0.1)

#     #for i in range(len(imgs)):
#     #    cv2.imwrite("pinwheel-{}.png".format(i), imgs[i])

#     del cam
#     del display
