#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Copyright (C) Incuvers, Inc - All Rights Reserved
#  Unauthorized copying of this file, via any medium is strictly prohibited
#  Proprietary and confidential
#  Written by Tim Spekens, David Sean
#
import uuid
import socket
import fcntl
import struct
import logging
from pathlib import Path


class FlaskHardwareInterface:
    """
    Class that holds everything important concerning communication in the webserver context

    """
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._logger.info("Instantiation successful.")

    def get_iface_list(self) -> list:
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
            self._logger.warning("No interfaces found in interface path: %s", iface_path)
        return ifaces

    def get_iface_hardware_address(self, _iface):
        """
        Get the hardware (MAC) address of the given interface
        :param iface:  iface (str) interface to return the mac off
        :return: str colon-delimited hardware address
        """
        if _iface not in self.get_iface_list():
            self._logger.warning("invalid interface: %s", _iface)
            return None
        try:
            mac = open('/sys/class/net/'+_iface+'/address').readline()
        except OSError:
            _hex = uuid.getnode()
            mac = ':'.join(['{:02x}'.format((_hex >> ele) & 0xff)
                            for ele in range(0, 8*6, 8)][::-1])
        return mac[0:17]

    def get_ip_address(self, _iface):
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

    def connects_to_internet(self, host="8.8.8.8", port=53, timeout=3):
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
        except socket.error as ex:
            print(ex)
            return False
        # I guess it worked? return True!
        return True
