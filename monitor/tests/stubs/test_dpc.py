#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright (C) Incuvers, Inc - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by David Sean
#
#import cv2
# import numpy as np
# import time

# from monitor.microscope.dpc import DPC
# from monitor.display import Display



# if __name__ == "__main__":

#     cam = DPC()
#     for idx in range(0):
#         light_pat = cam.get_pattern_as_array(idx).astype(np.uint8)
#         print(light_pat)
#         #cv2.imwrite("dpc_pattern-{}.png".format(idx), light_pat)

#     display = Display()
#     display.countdown()
#     #cam.live_stream(display.show)

#     imgs = cam.take_snaphot()
#     for repeat in range(1):
#         i = 0
#         for img in imgs:
#             print("mean: {}".format(np.mean(img)))
#             print("max: {}".format(np.max(img)))
#             print("min: {}".format(np.min(img)))
#             print(i)
#             display.show(img)
#             time.sleep(1)
#             #cv2.imwrite("dpc_full-{}.png".format(i), imgs[i])
#             i += 1

#     del cam
