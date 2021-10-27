# -*- coding: utf-8 -*-
"""
MQTT Exceptions
===============
Modified: 2021-06

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""


class ImageTopicError(Exception):
    def __init__(self, msg: str = "The image topic resolver detected a bad payload") -> None:
        self.message = msg
