#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Protocol
========
Modified: 2020-11

Dependencies:
-------------
```
from datetime import datetime
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
from typing import Any, Dict, List, Union


class Protocol:

    def __init__(self):
        self._id_set = False
        self._name_set = False
        self._repeats_set = False
        self._setpoints_set = False
        self._setpoint_index_set = True

    def __repr__(self) -> str:
        return "Protocol:{}".format(self.getattrs())

    def getattrs(self) -> Dict[str, Any]:
        """
        Iteratively get all object properties and values

        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        attributes: Dict[str, Any] = {}
        for k, v in vars(self).items():
            # only return property values
            if k.startswith('_{}__'.format(self.__class__.__name__)):
                json_key = k.split('__')[-1]
                attributes[json_key] = v 
        return attributes

    def setattrs(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            # repeats in the context of loops
            setattr(self, k, v)

    @property
    def initialized(self) -> bool:
        """
        Check if all properties have been initialized successfully

        :return: protocol init status
        :rtype: bool
        """
        initialized = all(
            [
                self._id_set,
                self._name_set,
                self._repeats_set,
                self._setpoints_set,
            ]
        )
        return initialized

    @property
    def id(self) -> int:
        """
        Get protocol id

        :return: protocol id
        :rtype: int
        """
        return self.__id

    @id.setter
    def id(self, protocol_id: int) -> None:
        """
        Set protocol id

        :param protocol_id: [description]
        :type protocol_id: int
        """
        self.__id = protocol_id
        self._id_set = True

    @property
    def name(self) -> str:
        """
        Get protocol name

        :return: protocol name 
        :rtype: str
        """
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set protocol name

        :param name: protocol name
        :type name: str
        """
        self.__name = name
        self._name_set = True

    @property
    def repeats(self) -> int:
        """
        Get protocol repeats

        :return: protocol repeats 
        :rtype: int
        """
        return self.__repeats

    @repeats.setter
    def repeats(self, repeat: int) -> None:
        """
        Set protocol repeats

        :param repeats: protocol repeats
        :type repeats: int
        """
        self.__repeats = repeat
        self._repeats_set = True

    @property
    def setpoints(self) -> List[Dict[str, Union[int, float]]]:
        """
        Get protocol setpoints

        :return: protocol setpoints 
        :rtype: List[Dict[str, Any]]
        """
        return self.__setpoints

    @setpoints.setter
    def setpoints(self, setpoints: List[Dict[str, Any]]) -> None:
        """
        Set protocol setpoints

        :param setpoints: protocol setpoints
        :type setpoints: List[Dict[str, Any]]
        """
        self.__setpoints = setpoints
        self._setpoints_set = True
