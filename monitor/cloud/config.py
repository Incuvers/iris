# -*- coding: utf-8 -*-
"""
MQTT Config
===========
Modified: 2021-06

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""


class MQTTConfig:
    # class definitions
    PORT = 8883
    # PORT = 443
    # TODO: this will come from the experiment id when the feature is properly implemented
    SLEEP = 5
    RECONNNECT = 10
    # timeout for netplan AP host in seconds
    CONNECTION_TIMEOUT = 60
    SHADOW_UPDATE_TIMEOUT = 5
