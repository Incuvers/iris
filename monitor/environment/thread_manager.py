#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Thread Manager
==============
Modified: 2021-03

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import gc
import os
import time
import psutil
import logging
from typing import Callable
from threading import Lock, Condition, Thread, enumerate, active_count, current_thread
from monitor.events.registry import Registry as events
from monitor.ui.static.settings import UISettings as uis


class ThreadManager:

    # set memory threshold as a percentage of RSS memory
    MEM_THRESH = 70
    process = psutil.Process(os.getpid())
    # singleton thread locks
    api_lock = Lock()
    arduino_lock = Lock()
    mqtt_lock = Lock()
    # condition variables
    gst_bus_condition = Condition()
    _logger = logging.getLogger(__name__)

    def __init__(self): ...

    def start(self) -> Thread:
        """
        Start thread monitor returning threading instance for join

        :return: thread monitor instance
        :rtype: threading.Thread
        """
        # tracemalloc.start()
        # gc.set_debug(gc.DEBUG_LEAK)
        gc.enable()
        self._logger.debug("gc has been enabled")
        # set main thread to high priority
        # self.process.nice(-1)
        # self._logger.debug("Nice process")
        monitor = Thread(name='monitor', target=self._monitor, daemon=True)
        monitor.start()
        return monitor

    def _monitor(self):
        """
        Main monitoring loop
        """
        while True:
            if self.process.memory_percent(memtype="rss") > self.MEM_THRESH:
                events.system_status.trigger(uis.STATUS_ALERT)
                self._logger.critical("RSS memory reached threshold. Triggering warning")
            self._logger.info("Process RSS Memory Footprint: %s MB",
                              round(self.process.memory_info().rss / 1e6, 2))
            self._logger.info("Process RSS Memory Usage: %s", round(
                self.process.memory_percent(memtype="rss"), 2))
            self._logger.info("Process CPU Usage: %s", self.process.cpu_percent(interval=None))
            # current = tracemalloc.take_snapshot()
            # top_stats = current.statistics('lineno')
            # self._logger.debug("Top 10 differences:")
            # for stat in top_stats[:10]:
            #     self._logger.debug(stat)
            for thread in enumerate():
                self._logger.debug("Thread Name: %s \t| Thread ID: %s",
                                   thread.name, thread.native_id)
            self._logger.debug("Active Threads: %s", active_count())
            self._logger.debug("--------------------------------------------------------------")
            time.sleep(5)

    @classmethod
    def lock(cls, lock: Lock) -> Callable:
        """
        Semaphore lock a function

        :param lock: threading lock (stored in this class)
        :type lock: threading.Lock
        :return: decorator
        :rtype: Callable
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs) -> None:
                with lock:
                    response = func(*args, **kwargs)
                return response
            return wrapper
        return decorator

    @classmethod
    def set_name(cls, name: str) -> Callable:
        """
        Set the active name for a thread for tracking

        :param name: thread name
        :type name: str
        :return: decorator
        :rtype: Callable
        """
        def decorator(func: Callable[..., None]) -> Callable:
            def wrapper(*args, **kwargs):
                alt_name = cls.assign_name(name)
                current_thread().name = alt_name
                func(*args, **kwargs)
            return wrapper
        return decorator

    @classmethod
    def threaded(cls, daemon: bool) -> Callable:
        """
        Start method as a named thread

        :param daemon: daemonize
        :type daemon: bool
        :return: decorator
        :rtype: Callable
        """
        def decorator(func: Callable[..., None]) -> Callable:
            def wrapper(*args, **kwargs):
                alt_name = cls.assign_name(func.__name__)
                Thread(
                    name=alt_name, target=func, args=args, kwargs=kwargs, daemon=daemon
                ).start()
                cls._logger.info("Thread %s invoked", alt_name)
            return wrapper
        return decorator

    @staticmethod
    def assign_name(name: str) -> str:
        """
        If the same thread name exists append a number to the thread name and increment
        """
        for thread in enumerate():
            if name == thread.name:
                try:
                    # check if thread name is a multiple
                    multiple = int(name.split('_')[1])
                except (IndexError, ValueError):
                    # if not start multiple index
                    name += '_1'
                else:
                    # if it is then increment multiple
                    name = name.split('_')[0]
                    name += '_' + str(multiple + 1)
        return name
