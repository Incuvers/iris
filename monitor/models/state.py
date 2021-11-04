# -*- coding: utf-8 -*-
"""
State Model Abstract
====================
Modified: 2021-11

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import json
from json import JSONDecodeError
from typing import Any, Dict
from abc import ABC, abstractmethod

class StateModel(ABC):

    def __init__(self, _id:int, filename:str) -> None:
        self.id = _id
        cache_base_path = os.environ.get('MONITOR_CACHE', default='/etc/iris/cache')
        os.makedirs(cache_base_path, mode=0o777, exist_ok=True)
        self.cache_path = f'{cache_base_path}/{filename}'

    @property
    def id(self) -> int:
        """
        Get state model id

        :return: protocol id
        :rtype: int
        """
        return self.__id

    @id.setter
    def id(self, _id: int) -> None:
        """
        Set state model id

        :param _id: state model id 
        :type _id: int
        """
        self.__id = _id


    @abstractmethod
    def serialize(self) -> Dict[str, Any]: ...

    @abstractmethod
    def deserialize(self, **kwargs) -> None: ...

    def cache(self) -> None:
        """
        Serialize contents and save to cache as a json file
        """
        with open(self.cache_path, 'w+') as json_file:
            cached_payload = self.serialize()
            json.dump(cached_payload, json_file)

    def load(self) -> None:
        """
        Load contents from json into state model
        """
        try:
            with open(self.cache_path, 'r') as json_file:
                device_payload: Dict[str, Any] = json.load(json_file)
        except (FileNotFoundError, JSONDecodeError):
            return
        self.deserialize(**device_payload)
