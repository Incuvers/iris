#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Capture
=======
Modified: 2020-10

The purpose of this class is to encapsulate the large image capture data inside an object that can be represented with a
minimal __repr__. In addition it houses the capture conversions required for posting to our api.

Dependencies:
-------------
```
import os
import sys
import logging
from typing import List
import numpy as np
from io import BytesIO
from PIL import Image
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import sys
import logging
from typing import List
import numpy as np
from io import BytesIO
from PIL import Image


class Capture:

    def __init__(self, captures: List[np.ndarray], dpc_exposure: int, gfp_capture: bool):
        self._logger = logging.getLogger(__name__)
        self.captures = captures
        # imaging profile associated with this capture instance
        self.dpc_exposure = dpc_exposure
        self.gfp_capture = gfp_capture
        self._logger.info("Created capture object with gfp: %s", self.gfp_capture)

    def get_raw(self, index: int):
        return self.captures[index]

    def get_processed(self, index: int) -> bytes:
        if index != 4:
            # processing dpc images
            converted_capture = self.captures[index]
            dpc_base_path = os.environ.get('MONITOR_DPC', default='/etc/iris/dpc')
            bg_fname = f'{dpc_base_path}/dpc_{self.dpc_exposure}_{index}.npz'
            converted_capture = self.background_normalize(converted_capture, bg_fname)
            # only convert to uint8 at the end to preserve data integrity
            converted_capture = converted_capture.astype(np.uint8)
        else:
            # processing gfp images (if applicable)
            converted_capture = self.captures[index].astype(np.uint8)
        self._logger.debug("Capture Size: %s", np.shape(converted_capture))
        to_return = Capture.nparray_to_png(converted_capture)
        self._logger.debug("File size: %s", sys.getsizeof(to_return) / 1024. / 1024.)
        return to_return

    def background_normalize(self, capture: np.ndarray, bg_fname: str) -> np.ndarray:
        """
        Normalize by a background image
        Both need to be the same shape
        """
        img = np.load(bg_fname)
        if img:
            try:
                background_img = img['data']
            except FileNotFoundError:
                self._logger.warning(
                    "DPC background: %s not found. Image is NOT normalized.", bg_fname)
            else:
                capture = capture / background_img * np.mean(background_img)
        return capture

    @staticmethod
    def crop_center(img: np.ndarray, cropx: int, cropy: int) -> np.ndarray:
        y, x, _ = img.shape
        startx = int(x // 2 - (cropx // 2))
        starty = int(y // 2 - (cropy // 2))
        return img[starty:starty + int(cropy), startx:startx + int(cropx), :]

    @staticmethod
    def nparray_to_png(nparray):
        """
        nparray has to be of shape (w, h,1)
        """
        # need to swap width and height #(1920, 2560,1)
        old_shape = np.shape(nparray)
        nparray = np.reshape(nparray, (old_shape[0], old_shape[1]))
        with BytesIO() as bytestream:
            image = Image.fromarray(nparray)
            image.save(bytestream, format='png', lossless=True)
            image_bytes = bytestream.getvalue()
        return image_bytes
