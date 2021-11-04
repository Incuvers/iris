# -*- coding: utf-8 -*-
"""
Device
======
Modified: 2021-06

Model object for device info

Dependencies:
-------------
```
import os
import json
import base64
from typing import Any, Dict, Optional
from monitor.logs.formatter import pformat
from monitor.models.state import StateModel
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import json
import base64
from typing import Any, Dict, Optional
from monitor.logs.formatter import pformat
from monitor.models.state import StateModel


class Device(StateModel):

    def __init__(self) -> None:
        """
        Set default device properties 
        """
        super().__init__(
            _id=os.environ.get('ID', default=""),
            filename='device.json'
        )
        self.name = "IRIS"
        self.jwt = None
        self.lab_id = None
        self.mqtt_status = False
        self.amqp_status = False
        self.jwt_payload = None

    def __repr__(self) -> str:
        return "Device: {}".format(pformat(self.serialize()))

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize object into json compatible dict

        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        return {
            'id': self.id,
            'name': self.name,
            'jwt': self.jwt,
            'lab_id': self.lab_id,
            'jwt_payload': self.jwt_payload
        }

    def deserialize(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

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
            encoded_jwt = jwt.split('')[-1]
            # get the payload section
            encoded_payload = encoded_jwt.split('.')[1]
            decoded_payload = base64.b64decode(encoded_payload + "===")
            self.jwt_payload = json.loads(decoded_payload)

    @property
    def jwt_payload(self) -> Optional[Dict[str,Any]]:
        """
        Get device jwt payload

        :return: device jwt payload
        :rtype: Optional[Dict[str,Any]]
        """
        return self.__jwt_payload

    @jwt_payload.setter
    def jwt_payload(self, payload: Optional[Dict[str,Any]]) -> None:
        """
        Set device jwt payload

        :param payload: parsed and decoded device jwt payload
        :type payload: Optional[Dict[str,Any]]
        """
        self.__jwt_payload = payload
        if payload is not None:
            self.lab_id = payload.get('lab_id')

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

    @property
    def registered(self) -> bool:
        """
        Get device registration status

        :return: device registration status
        :rtype: bool
        """
        return True if self.lab_id is not None else False

    @property
    def mqtt_status(self) -> bool:
        """
        Get mqtt connection status

        :return: mqtt connection status
        :rtype: bool
        """
        return self.__mqtt_status

    @mqtt_status.setter
    def mqtt_status(self, status: bool) -> None:
        """
        Set mqtt connection status

        :param status: mqtt connection status
        :type status: bool
        """
        self.__mqtt_status = status

    @property
    def amqp_status(self) -> bool:
        """
        Get amqp connection status

        :return: amqp connection status
        :rtype: bool
        """
        return self.__amqp_status

    @amqp_status.setter
    def amqp_status(self, status: bool) -> None:
        """
        Set amqp connection status

        :param status: amqp connection status
        :type status: bool
        """
        self.__amqp_status = status
