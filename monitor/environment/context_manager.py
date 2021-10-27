#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ContextManager
==============
Modified: 2020-05-19

This module applies environment variable context management for the app. We have two runtime
environments. Depending on the context: the system needs to handle environment variable validation
differently. This module has the power to terminate runtimes if the environment is not configured
properly.

Dependencies:
-------------
```
import os
import sys
import logging.config
import inspect
import hashlib
import platform
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os


class ContextManager:
    """
    Provides runtime context for distributed system components.
    Basically wraps os.environ in order to be mocked in unittests
    """

    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @staticmethod
    def get_env(environment: str, fallback=None) -> str:
        """
        :param environment: requested runtime environment variable
        :param fallback: value to return if the variable is not found

        :returns str: environment state variable i.e 'MONITOR_ENV' or fallback if not found
        """
        return os.environ.get(environment, fallback)

    @staticmethod
    def parse_id(readlines: list) -> str:
        """
        Method parses all characters that are non-conducive to an id character such as alphanumerics.
        This is in place since the local lab_id.txt can be manually modified by the user in
        the case of an error on the server side. Note that there are security measures in place if
        lab_id is changed to match another lab_id.

        :returns str: the string from the file as it pertains to id related characters.
        """
        return "".join(list(map(lambda x: x.rstrip(), readlines)))
