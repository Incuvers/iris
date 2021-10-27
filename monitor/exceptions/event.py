# -*- coding: utf-8 -*-
"""
Event and Pipeline Exceptions
=============================
Modified: 2021-06

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""


class NoListenersError(Exception):
    def __init__(self, msg: str = "Event triggered but no callbacks registered to event") -> None:
        self.message = msg


class PipelineError(Exception):
    def __init__(self, msg: str = "Pipeline length mismatch") -> None:
        self.message = msg
