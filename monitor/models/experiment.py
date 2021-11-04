# -*- coding: utf-8 -*-
"""
Experiment
==========
Modified: 2020-11

Model object for experiment info

Dependencies:
-------------
```
from typing import Any, Dict, Optional
from datetime import datetime
from monitor.logs.formatter import pformat
from monitor.models.state import StateModel
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from typing import Any, Dict, Optional
from datetime import datetime
from monitor.logs.formatter import pformat
from monitor.models.state import StateModel


class Experiment(StateModel):

    def __init__(self) -> None:
        super().__init__(
            _id=-1,
            filename='experiment.json'
        )
        self.protocol_id = -1
        self.imaging_profile_id = -1
        self.image_capture_interval = 0
        self.start_at = datetime.utcnow()
        self.end_at = datetime.utcnow()
        self.stop_at = None

    def __repr__(self) -> str:
        return "Experiment: {}".format(pformat(self.serialize()))

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize object into json compatible dict

        :return: object attributes and values
        :rtype: Dict[str, Any]
        """
        return {
            'id': self.id,
            'name': self.name,
            'protocol_id': self.protocol_id,
            'imaging_profile_id': self.imaging_profile_id,
            'image_capture_interval': self.image_capture_interval,
            'start_at': self.start_at.isoformat(),
            'end_at': self.end_at.isoformat(),
            'stop_at': self.stop_at.isoformat() if self.stop_at else None
        }

    def deserialize(self, **kwargs) -> None:
        """
        Iteratively set object properties
        """
        for k, v in kwargs.items():
            # NOTE: special case for stop_at (nullable)
            if k in ['end_at', 'start_at'] or (k == 'stop_at' and v is not None):
                iso_datetime_string: str = v  # ISO datetime
                attr = self.iso_to_time(iso_datetime_string)
            else:
                attr = v
            setattr(self, k, attr)

    @property
    def name(self) -> str:
        """
        Get experiment name

        :return: experiment name
        :rtype: str
        """
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        """
        Set experiment name

        :param name: experiment name
        :type name: str
        """
        self.__name = name

    @property
    def protocol_id(self) -> Optional[int]:
        """
        Get experiment protocol id

        :return: experiment protocol id
        :rtype: Optional[int]
        """
        return self.__protocol_id

    @protocol_id.setter
    def protocol_id(self, protocol_id: Optional[int]) -> None:
        """
        Set or unset experiment id protocol

        :param protocol_id: experiment protocol id
        :type protocol_id: Optional[int]
        """
        self.__protocol_id = protocol_id

    @property
    def imaging_profile_id(self) -> int:
        """
        Get experiment imaging profile id

        :return: experiment imaging profile id
        :rtype: int
        """
        return self.__imaging_profile_id

    @imaging_profile_id.setter
    def imaging_profile_id(self, imaging_profile_id: int) -> None:
        """
        Set experiment imaging profile id

        :param imaging_profile_id: experiment imaging profile id
        :type imaging_profile_id: int
        """
        self.__imaging_profile_id = imaging_profile_id

    @property
    def image_capture_interval(self) -> int:
        """
        Get experiment image capture interval (s)

        :return: image capture interval in seconds
        :rtype: int
        """
        return self.__image_capture_interval

    @image_capture_interval.setter
    def image_capture_interval(self, imaging_capture_interval: int) -> None:
        """
        Set experiment image capture interval

        :param imaging_capture_interval: set experiment capture in seconds
        :type imaging_capture_interval: int
        """
        self.__image_capture_interval = imaging_capture_interval

    @property
    def start_at(self) -> datetime:
        """
        Get experiment start time (UTC)

        :return: experiment start time in utc
        :rtype: datetime
        """
        return self.__start_at

    @start_at.setter
    def start_at(self, start_at: datetime) -> None:
        """
        Set experiment start time (UTC)

        :param start_at: experiment start time in utc 
        :type start_at: datetime
        """
        self.__start_at = start_at

    @property
    def end_at(self) -> datetime:
        """
        Get experiment end time (UTC)

        :return: experiment end time in utc
        :rtype: datetime
        """
        return self.__end_at

    @end_at.setter
    def end_at(self, end_at: datetime) -> None:
        """
        Set experiment end time (UTC)

        :param end_at: experiment end time in utc
        :type end_at: datetime
        """
        self.__end_at = end_at

    @property
    def stop_at(self) -> Optional[datetime]:
        """
        Get experiment stop time

        :return: experiment stop time 
        :rtype: Optional[datetime]
        """
        return self.__stop_at

    @stop_at.setter
    def stop_at(self, stop_at: Optional[datetime]) -> None:
        """
        Set experiment stop time

        :param value: experiment stop time
        :type value: datetime
        """
        self.__stop_at = stop_at

    @property
    def duration(self) -> float:
        """
        Get duration of the experiment in seconds

        :return: duration of experiment in seconds
        :rtype: float
        """
        # all values in utc
        if self.stop_at is not None:
            return (self.stop_at - self.start_at).total_seconds()
        return (self.end_at - self.start_at).total_seconds()

    @property
    def active(self) -> bool:
        """
        Get experiment state (active | inactive)

        :return: experiment state (active | inactive)
        :rtype: bool
        """
        if (self.end_at.timestamp() > datetime.now().timestamp() > self.start_at.timestamp()) and self.stop_at is None:
            return True
        return False

    @staticmethod
    def iso_to_time(time_string: str) -> datetime:
        """
        Helper method for conversion of ISO time string to datetime object

        :raises ValueError: if parsing of the string fails
        :return: datetime object representing time equivalent
        :rtype: datetime 
        """
        return datetime.fromisoformat(time_string)
