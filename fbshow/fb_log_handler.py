import logging
from .fbshow import FrameBufShow


class FBLogHandler(logging.StreamHandler):
    """
    A handler class which allows the cursor to stay on
    one line for selected messages
    """

    def __init__(self, output_device='/dev/fb0'):
        super().__init__()
        self.fb = FrameBufShow(output_device)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.fb.show(msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            self.handleError(record)
