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
import logging
from json import JSONDecodeError
from typing import Any, Dict, Union
from abc import ABC, abstractmethod

class StateModel(ABC):

    def __init__(self, _id:int, filename:str) -> None:
        self._logger = logging.getLogger(__name__)
        self.id = _id
        cache_base_path = os.environ.get('MONITOR_CACHE', default='/etc/iris/cache')
        os.makedirs(cache_base_path, mode=0o777, exist_ok=True)
        self.cache_path = f'{cache_base_path}/{filename}'
        self._logger.info("Created state model with cache path: %s", self.cache_path)

    def __eq__(self, o:object) -> bool:
        if hasattr(o, 'id') and hasattr(self, 'id'):
            return o.id == self.id  # type: ignore
        return False

    @property
    def id(self) -> Union[int, str]:
        """
        Get state model id

        :return: state model id
        :rtype: Union[int, str]
        """
        return self.__id

    @id.setter
    def id(self, _id: Union[int, str]) -> None:
        """
        Set state model id

        :param _id: state model id 
        :type _id: Union[int, str]
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
        self._logger.info("Cached state model: %s", self)

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
        self._logger.info("Loaded state model: %s", self)
