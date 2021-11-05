# -*- coding: utf-8 -*-
"""
System Helper Functions
=======================
Modified: 2021-11

This file is a collection standalone service (system-level) menu functions which can be accessed by any component.

Dependancies
------------
```
from monitor.environment.state_manager import StateManager
import time
import os
import logging
from typing import Optional
import numpy as np
import monitor.imaging.constants as IC
import uuid
import socket
import fcntl
import struct
from pathlib import Path
from monitor.sys import kernel
from monitor.sys import decorators
from monitor.cloud.mqtt import MQTT
from monitor.arduino_link.sensors import Sensors
from monitor.arduino_link.icb_logger import ICBLogger
from monitor.microscope.microscope import Microscope as scope
from monitor.events.registry import Registry as events
from monitor.flash_service.flash_service import FlashService
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.thread_manager import ThreadManager as tm
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import os
import uuid
import socket
import fcntl
import struct
import logging
from pathlib import Path
from typing import Optional
from monitor.models.device import Device
from monitor.models.protocol import Protocol
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile

_logger = logging.getLogger(__name__)

def test_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3):
    """
    Tests internet connectivity
    Test intenet connectivity by checking with Google
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    :param host: (str) the host to test connection
    :param port: (int) the port to use
    :param timeout:
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
    except socket.error:
        return False
    return True


def get_iface_list() -> list:
    """
    Get the list of interfaces
    :return:  ifaces (list) : a list of interface identifiers (string)
    """
    # define the path
    iface_path = Path('/sys/class/net').resolve()
    # parse all paths from interface path
    iface_paths = iface_path.glob("*")
    # if file doesnt exist we skip (ie an empty list means path was not resolved)
    ifaces_dirs = [x for x in iface_paths if x.is_dir()]
    ifaces = list(map(
        lambda x: x.parts[-1], ifaces_dirs
    ))
    if len(ifaces) == 0:
        _logger.warning("No interfaces found in interface path: %s", iface_path)
    return ifaces


def get_iface_hardware_address(_iface: str) -> Optional[str]:
    """
    Get the hardware (MAC) address of the given interface
    :param iface:  iface (str) interface to return the mac off
    :return: str colon-delimited hardware address
    """
    if _iface not in get_iface_list():
        _logger.warning("invalid interface: %s", _iface)
        return None
    try:
        mac = open('/sys/class/net/' + _iface + '/address').readline()
    except OSError:
        _hex = uuid.getnode()
        mac = ':'.join(['{:02x}'.format((_hex >> ele) & 0xff)
                        for ele in range(0, 8 * 6, 8)][::-1])
    return mac[0:17]


def get_ip_address(_iface: str) -> str:
    """
    Get the primary IP address
    :return: (str) standard representation of the device's IP address
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip_addr = socket.inet_ntoa(
            fcntl.ioctl(
                sock.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', bytes(_iface[:15], encoding='utf8'))
            )[20:24]
        )
    except OSError:
        ip_addr = "No IP"
    return ip_addr

def write_img(img: bytes, filename:str) -> None:
    """
    Write image file to disk

    :param img: byte encoded image
    :type img: bytes
    :param filename: image filename
    :type filename: str
    """
    base_path = os.environ.get('COMMON', default='/etc/iris')
    img_path = f'{base_path}/{filename}'
    with open(img_path, 'wb') as img_file:
        img_file.write(img)

def read_lab_id() -> Optional[int]:
    """
    Read cached lab id from disk

    :return: lab id if specified
    :rtype: Optional[int]
    """
    try:
        with open(os.environ.get('MONITOR_CERTS', default='/etc/iris/certs') + '/lab_id.txt', 'r') as fp:
            contents = fp.readlines()
    except FileNotFoundError:
        return None
    return int("".join(list(map(lambda x: x.rstrip(), contents))))

def write_lab_id(lab_id: Optional[int]) -> None:
    """
    Writes lab_id to the local lab_id file (lab_id.txt)
    """
    fp = os.environ.get('MONITOR_CERTS', default='/etc/iris/certs') + '/lab_id.txt'
    if lab_id is None and os.path.isfile(fp):
        os.remove(fp)
        return
    with open(fp, 'w+') as fp:
        fp.write(f"{lab_id}")

def clear_cache() -> None:
    """
    Clear state model cache
    """
    cache_base_path = os.environ.get('MONITOR_CACHE', default='/etc/iris/cache')
    for filename in [Device.FILENAME, Experiment.FILENAME, ImagingProfile.FILENAME, Protocol.FILENAME]:
        fp = f'{cache_base_path}/{filename}'
        try:
            os.remove(fp)
        except FileNotFoundError:
            pass

def clear_thumbnail() -> None:
    """
    Remove thumbnail image from COMMON
    """
    # remove cached thumbnail image
    filename = os.environ.get('COMMON', default='/etc/iris') + "/thumbnail.png"
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass
