# -*- coding: utf-8 -*-
"""
Microscope Exceptions
=====================
Modified: 2021-07

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""


class MicroscopeError(Exception):
    def __init__(self, msg: str = "Microscope encountered an error") -> None:
        self.message = msg


class GSTPipelineError(MicroscopeError):
    def __init__(self, msg: str = "GST pipeline encountered an error") -> None:
        self.message = msg


class GSTDeviceError(MicroscopeError):
    def __init__(self, msg: str = "A problem occured with the GST device.") -> None:
        self.message = msg


class NoGSTDeviceError(GSTDeviceError):
    def __init__(self, msg: str = "A problem occured with the GST device.") -> None:
        self.message = msg


class PropertyError(GSTDeviceError):
    def __init__(self, msg: str = "GST device probe failed") -> None:
        self.message = msg


class MultipleGSTDevicesError(GSTDeviceError):
    def __init__(self, msg: str = "Only one GST device is supported") -> None:
        self.message = msg


class UvcdynctrlError(MicroscopeError):
    def __init__(self, msg: str = "Uvcdynctrl failed to initialize") -> None:
        self.message = msg


class ChannelError(MicroscopeError):
    def __init__(self, msg: str = "Channel failed to initialize") -> None:
        self.message = msg


class LightingError(MicroscopeError):
    def __init__(self, msg: str = "Microscope lighting modules failed to initialize") -> None:
        self.message = msg
