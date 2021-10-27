#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fluorescence Hardware
=====================
Modified: 2021-03

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

class FluorescenceHardware:
    """ Hardware definitions for the Fluorescence LED
    Some new boards (ICB 2.3 and higher) have a logic inverter chip.
    This means we need to invert the ACTIVE_HIGH boolean between these boards
    and the former once.
    This class reads from hardware.env file (read at at init), and flips the
    boolean depending on the precence of the inverter. The legacy case
    (without a hardware definition) uses no inverter and ACTIVE_HIGH=True.
    """

    TRIGGER = 7
    ACTIVE_HIGH = False
    # 20 second timeout for GFP LED
    GFP_BURNOUT = 120
    # 60 second cooldown for GFP LED
    GFP_COOLDOWN = 240
