# -*- coding: utf-8 -*-
"""
Monitor __init__
================
Modified: 2021-11

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import logging
import logging.config

from monitor.__version__ import __version__

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s"
)
logging.info("Incuvers™ Monitor Version: %s", __version__)
