# -*- coding: utf-8 -*-
"""
Setpoint Model
==============
Modified: 2021-11

Dependencies:
-------------
```
from typing import Any, Dict
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from typing import Any, Dict


class Setpoint:
    def __init__(self) -> None:
        self.index = 0
        self.duration = 0
        self.CP = 0.0
        self.TP = 0.0
        self.OP = 0.0

    def serialize(self) -> Dict[str, Any]:
        return {
            'index': self.index,
            'duration': self.duration,
            'CP': self.CP,
            'TP': self.TP,
            'OP': self.OP,
        }
    
    def deserialize(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def index(self) -> int:
        """
        Get setpoint index

        :return: setpoint index
        :rtype: int 
        """
        return self.__index

    @index.setter
    def index(self, idx:int) -> None:
        """
        Set setpoint index

        :param idx: setpoint index
        :type idx: int 
        """
        self.__index = idx 

    @property
    def duration(self) -> int:
        """
        Get setpoint duration

        :return: setpoint duration
        :rtype: int 
        """
        return self.__duration

    @duration.setter
    def duration(self, duration:int) -> None:
        """
        Set setpoint duration

        :param duration: setpoint duration
        :type duration: int 
        """
        self.__duration = duration

    @property
    def TP(self) -> float:
        """
        Get temperature setpoint

        :return: temperature setpoint
        :rtype: float
        """
        return self.__TP
    
    @TP.setter
    def TP(self, setpoint:float) -> None:
        """
        Set temperature setpoint

        :param setpoint: temperature setpoint
        :type setpoint: float
        """
        self.__TP = setpoint

    @property
    def CP(self) -> float:
        """
        Get co2 setpoint

        :return: co2 setpoint
        :rtype: float
        """
        return self.__CP

    @CP.setter
    def CP(self, setpoint:float) -> None:
        """
        Set co2 setpoint

        :param setpoint: co2 setpoint
        :type setpoint: float
        """
        self.__CP = setpoint

    @property
    def OP(self) -> float:
        """
        Get o2 setpoint

        :return: o2 setpoint
        :rtype: float
        """
        return self.__OP

    @OP.setter
    def OP(self, setpoint:float) -> None:
        """
        Set o2 setpoint

        :param setpoint: o2 setpoint
        :type setpoint: float
        """
        self.__OP = setpoint
