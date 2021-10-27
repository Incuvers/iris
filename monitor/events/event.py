#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Event
=====
Modified: 2021-05

Dependencies:
-------------
```
from typing import Callable, Optional, Tuple, TypeVar, Generic, List
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import logging

from typing import Callable, Optional, Tuple, TypeVar, Generic, List

_T = TypeVar('_T', bound=Callable[..., None])


class Event(Generic[_T]):
    def __init__(self, name: str) -> None:
        """
        name = [
            (callback<T>, priority<int>, conditional<Callable[..., bool]>),
            (callback<T>, priority<int>, conditional<Callable[..., bool]>),
            (callback<T>, priority<int>, conditional<Callable[..., bool]>),
            ...
        ]
        """
        self._logger = logging.getLogger(__name__)
        self.name = name
        # Create an empty list with items of type T
        self.registry: List[Tuple[_T, int, Optional[Callable[..., bool]]]] = []
        self._logger.info("Event: %s initialized.", self)

    def __str__(self) -> str:
        return self.name + ": " + str(self.registry)

    def register(self, callback: _T, priority: int = 1, condition: Optional[Callable[..., bool]] = None) -> None:
        """
        Register a callback function to this event with a priority level and an optional conditional
        function to determine execution action.

        :param callback: <T> function with T parameter and return type schema
        :param priority: <int> 1 | 0 representing the priority level of execution
        :param conditional: <Callable | None> 
        """
        # append callback, priority and condition to event registry
        self.registry.append((callback, priority, condition))
        # sort events by priority level
        self.registry.sort(key=lambda t: t[1])
        self._logger.info("Event: %s registered a callback @ priority: %s", self.name, priority)

    def trigger(self, *args, **kwargs) -> None:
        """
        Trigger event callbacks with args conditional is true or unset. Note: in python 3.10 with the
        introduction of typing.ParamSpec we should be able to provide typing and intellisense support
        for this method.
        """
        self._logger.debug("Executing %s", self.name)
        if len(self.registry) == 0:
            self._logger.warning("No function in registry %s", self.name)
        for event in self.registry:
            # unpack the event tuple
            callback, _, conditional = event
            if conditional is None or conditional(*args, **kwargs):
                try:
                    callback(*args, **kwargs)
                except BaseException as exc:
                    self._logger.exception(
                        "Callback encountered an exception during execution:\n%s", exc)
                    continue
                self._logger.info("%s execution successful", callback)
            else:
                self._logger.info("Masked callback trigger due to unsatisfied conditional")
