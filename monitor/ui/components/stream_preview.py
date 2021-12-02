# -*- coding: utf-8 -*-
"""
Stream Preview
==============
Modified: 2021-07

Dependencies:
-------------
```
import pygame
import numpy as np

from typing import Optional
from monitor.ui.components.widget import Widget
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.microscope.camera.gst_pipeline import GSTPipeline
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import pygame
import numpy as np

from typing import Optional
from monitor.ui.components.widget import Widget
from monitor.ui.static.settings import UISettings as uis
from monitor.ui.components.loading_wheel import LoadingWheel
from monitor.microscope.camera.stream_pipeline import StreamPipeline


class StreamPreview(Widget):

    PAUSE_TIMEOUT = 120

    """
    Preview window for rendering microscope streams
    """

    def __init__(self, width: int, height: int, pipeline: StreamPipeline, stats: bool = False):
        self.stats = stats
        self.disable = False
        # when the stream stops we cache the last image as a loading preview
        self.last_frame = None
        # for analytics
        self.last_capture = None
        self.pause_counter = 0
        self.paused = False
        # for offset computation
        self.x = 0
        self.y = 0
        self.load_icon = LoadingWheel(
            centering=(300, 300),
            scaling=(50, 50),
        )
        self.pipeline = pipeline
        super().__init__(width, height)

    def pause(self):
        """
        Enable the loading wheel and lock the last frame
        """
        self.paused = True
        self.load_icon.start()

    def resume(self):
        """
        Disable the loading wheel and unlock the stream
        """
        self.paused = False
        self.load_icon.stop()

    def draw_empty(self):
        """
        Draw empty rectangle over the preview window
        """
        pygame.draw.rect(
            self.surf,
            uis.INCUVERS_BLACK,
            pygame.Rect(0, 0, self.width, self.height)
        )
        self.load_icon.start()
        # update load wheel (keep outside of conditionals)
        load_wheel = self.load_icon.update()
        if load_wheel is not None:
            self.surf.blit(load_wheel[0], load_wheel[1])

    def render_surface(self, buffer: np.ndarray) -> pygame.Surface: # type: ignore
        """
        Process microscope stream buffer data into a pygame surface

        :param buffer: image data as a numpy array
        :return: pygame surface
        """
        # perform fitting processing
        # TODO: FIX HACK FOR PYGAME
        capture = np.reshape(buffer, (buffer.shape[0], buffer.shape[1]))
        capture = capture.transpose()
        capture = np.reshape(capture, (capture.shape[0], capture.shape[1], 1))
        transform = np.repeat(capture, 3, axis=2)
        # update offsets
        self.x, self.y = transform.shape[0], transform.shape[1]
        # pygame expects pixels to be RGB tuples, but the image is a single greyscale value
        # just last axis it 3 times for greyscale -> RGB conversion
        img_surface = pygame.surfarray.make_surface(transform)
        # ensure image is centered (ie cropped equally on all sides). This is important in order to
        # ensure the qualities that were centered in the preview is also centered in the final form
        return img_surface

    def extract_buffer(self) -> Optional[np.ndarray]:
        """
        Get an image from the pipeline buffer, if no image is available use the last available capture

        :return: np.array
        """
        if self.pipeline is None:
            return None
        try:
            capture = self.pipeline.img_buffer.pop()
        except IndexError:
            # use as a placholder for capture
            capture = self.last_capture
        else:
            # update the last capture
            self.last_capture = capture
            self.load_icon.stop()
        return capture

    def render_stats(self):
        """
        Render the image stats as an overlay
        """
        max_px = int(np.max(self.last_capture[:, :, 0])) if self.last_capture is not None else 0
        min_px = int(np.min(self.last_capture[:, :, 0])) if self.last_capture is not None else 0
        ave_px = np.mean(self.last_capture[:, :, 0]) if self.last_capture is not None else 0
        self._render_text("max: {0:d}".format(max_px), 5, 20, uis.INCUVERS_BLUE)
        self._render_text("min: {0:d}".format(min_px), 25, 20, uis.INCUVERS_BLUE)
        self._render_text("ave: {0:.0f}".format(ave_px), 45, 20, uis.INCUVERS_BLUE)

    def redraw(self):
        """
        Preview rendering loop
        """
        # if the preview is paused do not extract a new image
        if not self.paused:
            # try and grab a new image from the pipeline buffer
            capture = self.extract_buffer()
            # speedup for first load
            if capture is None:
                self.draw_empty()
                return
            # TODO: Fast High Contrast Streaming
            # min=np.percentile(capture, 0.1)
            # max=np.percentile(capture, 99.9)
            # scale = 255./(max-min)
            # print(min)
            # print(scale)
            # transpile the microscope capture buffer into a pygame surface
            # offset and rescale using those numbers
            # capture=(capture - 102.0) * 7.7272727272727275
            # capture=np.clip(capture, 0, 255)
            img = self.render_surface(capture)
        else:
            self.pause_counter += 1
            if self.pause_counter > self.PAUSE_TIMEOUT:
                self.pause_counter = 0
                self.paused = False
            # if we are paused use the last available frame as a preview
            if self.last_frame is not None:
                img = self.last_frame
            else:
                self.draw_empty()
                return
        # cache the last pre-processed frame
        self.last_frame = img
        # blit image
        self.surf.blit(img, (0, 0), ((self.x - 600) / 2, (self.y - 724) / 2, 600, 724))
        # render stats if set
        if self.stats:
            self.render_stats()
        # update load wheel (keep outside of conditionals)
        load_wheel = self.load_icon.update()
        if load_wheel is not None:
            self.surf.blit(load_wheel[0], load_wheel[1])
