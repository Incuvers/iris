# -*- coding: utf-8 -*-
"""
Api Cache
============
Updated: 2021-05



Dependencies:
-------------
```
import os
import logging.config
import json
from pathlib import Path
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import copy
import logging
from functools import partial
from typing import Callable, Dict
from collections import OrderedDict


class ProxyCache:

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._proxy_buffer: Dict[int, partial] = OrderedDict()
        self._logger.info("%s instantiated", __name__)

    def cache(self, proxy_request: Callable[..., None], *args, **kwargs):
        """
        Saves failed api request as a FIFO queue. We want to save the order of the requests but want
        to replace args and kwargs of duplicate request types (api request functions) with the
        recent changes.
        """
        # the request types are matched by the function names
        self._proxy_buffer[proxy_request.__hash__()] = partial(proxy_request, *args, **kwargs)
        self._logger.debug("Cached failed api request with args: %s kwargs: %s", args, kwargs)

    def execute(self) -> None:
        """
        Executes all cached api requests in FIFO ordering.
        """
        # the api_requests may change dynamically during the loop if a request fails
        # so we create a deepcopy of the buffer data struct and iterate over that
        self._logger.debug("Starting cache execution.")
        buf = copy.deepcopy(self._proxy_buffer)
        for hash, request in buf.items():
            # execute the request wrapper plus any subsequent function redirects
            try:
                request()
            except (ConnectionError, ReferenceError, TimeoutError, KeyError) as exc:
                # log failure and keep the request in the cache for next retry
                self._logger.info("Exception occured during cached request execution:\n%s", exc)
            else:
                # remove successful requests from the master buffer
                self._proxy_buffer.pop(hash)
        self._logger.debug("Completed cache execution")
