# -*- coding: utf-8 -*-
"""
Log Object Formatter
====================
Modified: 2021-10
"""


import json
from typing import Any


def pformat(payload: Any) -> str:
    """
    Format payloads for logging
    :param payload: payload to format
    :type payload: Any
    :return: logging output
    :rtype: str
    """
    return "\n" + json.dumps(payload, indent=2)
