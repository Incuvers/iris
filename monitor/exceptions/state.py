# -*- coding: utf-8 -*-
"""
Monitor State Exceptions
========================
Modified: 2021-08

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""


class StateError(Exception):
    def __init__(self, msg: str = "The system state gave an unexpected result") -> None:
        self.message = msg
