#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kernel Command Invoker
======================
Modified: 2021-03

Dependancies
------------
```
import subprocesss
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import subprocess

def os_cmd(cmd:str) -> str:
    """
    Wrapper for executing kernel commands and returning the exit status through OSError.
    NOTE: all kernel calls should route to this function to homogenize exception handles. This
    function pipes stderr through stdout so the kernel error message be read through our app loggers

    :param cmd: string of command 
    :raises OSError: if command returns a non-zero exit status
    :returns: utf-8 decoded string result of os call
    """
    # execute subprocess call and pipe stderr / stdout through OSError exception
    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        exception = OSError()
        exception.errno = exc.returncode
        exception.strerror = exc.stdout.decode('utf-8')
        raise exception from exc
    return result.decode('utf-8')
