#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline
========
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
from typing import Any, Callable, Tuple, List
from monitor.exceptions.event import NoListenersError, PipelineError


class Pipeline:
    def __init__(self, name: str, length: int) -> None:
        self._logger = logging.getLogger(__name__)
        self.name = name
        self.length = length
        # Create an empty list with items of type T
        self.registry: List[Callable[..., Any]] = []
        self._logger.info("Created pipeline %s", self.name)

    def __str__(self) -> str:
        return self.name + ": " + ' | '.join([fn.__str__() for fn in self.registry])

    def stage(self, callback: Callable[..., Any], index: int) -> None:
        """
        Add a function to a stage in the pipeline at specified index. The return type of the function must
        match the paramspec of the proceeding function and its paramspec must match the return type of the
        preceeding function.

        :param callback: pipeline callback
        :type callback: Callable[...,Any]
        :param index: function execution location
        :type index: int
        """
        self.registry.insert(index, callback)
        self._logger.info(
            "Pipeline: {} staged a callback: {} @ index: {}".format(self.name, callback, index))

    def begin(self, *pargs, **pkwargs) -> None:
        """
        Begin pipeline execution with required arguments for the first function in the pipeline.
        """
        self._logger.info("Beginning %s pipeline", self.name)
        if len(self.registry) == 0:
            raise NoListenersError
        elif len(self.registry) < self.length:
            raise PipelineError
        # iterate through registry callbacks
        for index, stage in enumerate(self.registry):
            try:
                if pargs is None: ret = stage()
                # NOTE: accept kwargs for first pipeline for clarity -> until Paramspec arrives in python 3.10
                elif index == 0: ret = stage(*pargs, **pkwargs)
                else: ret = stage(*pargs)
            except BaseException as exc:
                # stop pipeline on any unhandled exception
                self._logger.exception(
                    "Pipeline halted due to exception encountered during execution:\n{}".format(exc))
                return
            # construct args from ret
            if ret is None or isinstance(ret, Tuple): pargs = ret
            else: pargs = (ret,)
            self._logger.info("Pipeline stage %s | %s successful", stage, index)
