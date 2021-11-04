# -*- coding: utf-8 -*-
"""
Protocol
========
Modified: 2021-11

Dependencies:
-------------
```
from datetime import datetime
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
from typing import Any, Dict, List
from monitor.models.setpoint import Setpoint
from monitor.models.state import StateModel

class Protocol(StateModel):

    def __init__(self):
        super().__init__(
            _id=-1,
            filename='protocol.json'
        )
        self.name = "Default Protocol"
        self.setpoints = []
        self.repeats = 0

    def __repr__(self) -> str:
        return "Protocol:{}".format(self.serialize())

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize object into json compatible dict

        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        return {
            'id': self.id,
            'name': self.name,
            'repeats': self.repeats,
            'setpoints': [ setpoint.serialize() for setpoint in self.setpoints ],
        }

    def deserialize(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            if k == 'setpoints':
                # translate setpoints payload to setpoint models
                setpoints: List[Setpoint] = []
                for sp in v:
                    setpoint = Setpoint()
                    setpoint.deserialize(**sp)
                    setpoints.append(setpoint)
                setattr(self, k, setpoints)
            setattr(self, k, v)

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

    @property
    def setpoints(self) -> List[Setpoint]:
        """
        Get protocol setpoints

        :return: protocol setpoints 
        :rtype: List[Setpoint]
        """
        return self.__setpoints

    @setpoints.setter
    def setpoints(self, setpoints: List[Setpoint]) -> None:
        """
        Set protocol setpoints

        :param setpoints: protocol setpoints
        :type setpoints: List[Setpoint]
        """
        self.__setpoints = setpoints
