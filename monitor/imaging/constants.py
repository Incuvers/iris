# -*- coding: utf-8 -*-
"""
System Imaging Constants
========================

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from typing import Dict, Union

# transfer function dpc exposure to gradient


def dpc_grade_to_exposure(grade: int) -> int:
    return 130 * grade + 2000

# transfer function gfp exposure to gradient


def gfp_grade_to_exposure(grade: int) -> int:
    return 19000 * grade + 100000

# transfer function dpc grade to exposure


def dpc_exposure_to_grade(exp: int) -> int:
    return int((exp - 2000) // 130)

# transfer function gfp grade to exposure


def gfp_exposure_to_grade(exp: int) -> int:
    return int((exp - 100000) // 19000)


# just for dpc background calibration
DPC_GAIN = 4
DPC_BRIGHTNESS = 168
DPC_SCAN_MODE = 0
GFP_GAIN = 60
GFP_BRIGHTNESS = 168
GFP_SCAN_MODE = 0
INNER_RADIUS = 3.0
OUTER_RADIUS = 4.0
GAIN_MIN = 4
GAIN_MAX = 63
BRIGHTNESS_MIN = 0
BRIGHTNESS_MAX = 4096
DEFAULT_DPC_EXPOSURE = dpc_grade_to_exposure(grade=50)
DEFAULT_GFP_EXPOSURE = gfp_grade_to_exposure(grade=50)
DPC_EXPOSURE_MIN = dpc_grade_to_exposure(grade=0)
DPC_EXPOSURE_MAX = dpc_grade_to_exposure(grade=100)
GFP_EXPOSURE_MIN = gfp_grade_to_exposure(grade=0)
GFP_EXPOSURE_MAX = gfp_grade_to_exposure(grade=100)

DEFAULT_IP_PAYLOAD: Dict[str, Union[str, bool, int, float]] = {
    'gfp_capture': False,
    'dpc_exposure': DEFAULT_DPC_EXPOSURE,
    'dpc_exposure_min': DPC_EXPOSURE_MIN,
    'dpc_exposure_max': DPC_EXPOSURE_MAX,
    'gfp_exposure_min': GFP_EXPOSURE_MIN,
    'gfp_exposure_max': GFP_EXPOSURE_MAX,
    'gfp_exposure': DEFAULT_GFP_EXPOSURE,
    'dpc_brightness': DPC_BRIGHTNESS,
    'dpc_gain': DPC_GAIN,
    'gfp_brightness': GFP_BRIGHTNESS,
    'gfp_gain': GFP_GAIN,
    'gain_min': GAIN_MIN,
    'gain_max': GAIN_MAX,
    'brightness_min': BRIGHTNESS_MIN,
    'brightness_max': BRIGHTNESS_MAX,
    'dpc_inner_radius': INNER_RADIUS,
    'dpc_outer_radius': OUTER_RADIUS
}
