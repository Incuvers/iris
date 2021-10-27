#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright (C) Incuvers, Inc - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by David Sean
#
# import numpy as np
# import time
# from monitor.microscope.fluorescence import Fluorescence
# from monitor.display import Display



# if __name__ == "__main__":

#     cam = Fluorescence()

#     display = Display()
#     display.countdown()
#     # cam.live_stream(display.show)

#     img = cam.take_snapshot()
#     display.show(img)
#     print("mean: {}".format(np.mean(img)))
#     print("max: {}".format(np.max(img)))
#     print("min: {}".format(np.min(img)))
#     time.sleep(5)

#     #cv2.imwrite("fluorescence-short.png", img)

#     del fluo
#     del display
