#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decorators
==========

This module hosts a collection of system decorators which can be accessed by any component.

Dependancies
------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
from monitor.ui.static.settings import UISettings as uis
from typing import Callable
from monitor.events.registry import Registry as events


def cache(proxy: Callable[..., None]):
    def wrapper(self, *args, **kwargs) -> None:
        try:
            proxy(self, *args, **kwargs)
        except (ConnectionError, ReferenceError, TimeoutError, KeyError):
            self.cache.cache(proxy, self, *args, **kwargs)
            self._logger.info("Cached failed proxy request")
            events.system_status.trigger(status=uis.STATUS_OK)
    return wrapper


def load(func):
    """
    """
    def wrapper(*args, **kwargs):
        events.start_load.trigger(True)
        func(*args, **kwargs)
        events.start_load.trigger(False)
    return wrapper

def splash(func):
    """
    Runs function on a new thread to display loading screen
    """
    def wrapper(*args, **kwargs):
        events.splash_load.trigger(True)
        func(*args, **kwargs)
        events.splash_load.trigger(False)
    return wrapper
