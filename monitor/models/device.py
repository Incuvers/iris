#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Device
======
Modified: 2021-06

Model object for device info

Dependencies:
-------------
```
import json
import base64
from typing import Optional
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import json
import base64
from typing import Any, Dict, Optional


class Device:

    def __init__(self) -> None:
        """
        Set default device properties 
        """
        self._id_set = False
        self._name_set = False
        self._connected_set = False
        self._jwt_set = False
        self._jwt_payload_set = False
        self._lab_id_set = False
        self.connected = False
        self.id = os.environ['ID']
        self.name = "Welcome to IRIS"
        self.jwt = None
        self.jwt_payload = None
        self.lab_id = None 

    def __repr__(self) -> str:
        return "Device: {}".format(self.getattrs())

    def getattrs(self) -> Dict[str, Any]:
        """
        Iteratively get all object properties and values

        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        attributes: Dict[str, Any] = {}
        for k, v in vars(self).items():
            if k.startswith('_{}__'.format(self.__class__.__name__)):
                attributes[k.split('__')[-1]] = v
        return attributes

    def setattrs(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def initialized(self) -> bool:
        """
        Check if all properties have been initialized successfully

        :return: device init status
        :rtype: bool
        """
        initialized = all(
            [
                self._id_set,
                self._name_set,
                self._connected_set,
                self._jwt_payload_set,
                self._jwt_set,
                self._lab_id_set,
            ]
        )
        return initialized

    @property
    def id(self) -> str:
        """
        Get device id (id)

        :return: device id
        :rtype: str
        """
        return self.__id

    @id.setter
    def id(self, device_id: str) -> None:
        """
        Set device id (id)

        :param device_id: device id
        :type device_id: str
        """
        self.__id = device_id
        self._id_set = True

    @property
    def name(self) -> str:
        """
        Get device name

        :return: device name
        :rtype: str
        """
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set device name

        :param name: device name
        :type name: str
        """
        self.__name = name
        self._name_set = True

    @property
    def jwt(self) -> Optional[str]:
        """
        Get device jwt

        :return: device jwt
        :rtype: Optional[str]
        """
        return self.__jwt

    @jwt.setter
    def jwt(self, jwt: Optional[str]) -> None:
        """
        Set device jwt, payload_jwt and registered status

        :param jwt: device jwt
        :type jwt: Optional[str]
        """
        if jwt is None:
            self.__jwt = None
        else:
            self.__jwt = jwt
            # remove the bearer bit
            encoded_jwt = jwt.split(' ')[-1]
            # get the payload section
            encoded_payload = encoded_jwt.split('.')[1]
            decoded_payload = base64.b64decode(encoded_payload + "===")
            self.jwt_payload = json.loads(decoded_payload)
        self._jwt_set = True

    @property
    def jwt_payload(self) -> Optional[dict]:
        """
        Get device jwt payload

        :return: device jwt payload
        :rtype: Optional[dict]
        """
        return self.__jwt_payload

    @jwt_payload.setter
    def jwt_payload(self, payload: Optional[dict]) -> None:
        """
        Set device jwt payload

        :param payload: parsed and decoded device jwt payload
        :type payload: Optional[dict]
        """
        self.__jwt_payload = payload
        if payload is not None:
            self.lab_id = payload.get('lab_id')
        self._jwt_payload_set = True

    @property
    def lab_id(self) -> Optional[int]:
        """
        Get device lab id

        :return: device lab id
        :rtype: Optional[int]
        """
        return self.__lab_id

    @lab_id.setter
    def lab_id(self, lab_id: Optional[int]) -> None:
        """
        Set device lab id

        :param lab_id: device lab id
        :type lab_id: Optional[int]
        """
        self.__lab_id = lab_id
        self._lab_id_set = True

    @property
    def registered(self) -> bool:
        """
        Get device registration status

        :return: device registration status
        :rtype: bool
        """
        return True if self.lab_id is not None else False

    @property
    def connected(self) -> bool:
        """
        Get device connection status

        :return: device connection status
        :rtype: bool
        """
        return self.__connected

    @connected.setter
    def connected(self, status: bool) -> None:
        """
        Set device connection status

        :param status: device connection status 
        :type status: bool
        """
        self.__connected = status
        self._connected_set = True
