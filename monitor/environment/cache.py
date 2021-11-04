# -*- coding: utf-8 -*-
"""
System Cache
============
Updated: 2021-05

Cache saves fetched device, experiment, protocol and imaging profile payloads to disk. This allows
the experiment data and protocols to persist through a system reboot and from the cloud.
Dependencies:
-------------
```
import os
import logging.config
import json
from pathlib import Path
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import os
import copy
import json
import logging
from typing import Optional, Union
from datetime import datetime, timezone
from json.decoder import JSONDecodeError

from monitor.models.device import Device
from monitor.models.protocol import Protocol
from monitor.models.experiment import Experiment
from monitor.events.registry import Registry as events
from monitor.models.imaging_profile import ImagingProfile
from monitor.environment.context_manager import ContextManager
from monitor.environment.registry import StateRegistry as sr


class SystemCache:

    def __init__(self):
        # bind logging to config file
        self._logger = logging.getLogger(__name__)
        events.avatar_pipeline.stage(self.write_device_avatar, 0)
        events.cache_thumbnail.register(self.write_thumbnail)
        # initialize filesystem
        with ContextManager() as context:
            os.makedirs(context.get_env('MONITOR_CACHE'), mode=0o777, exist_ok=True)
        self._logger.info("%s instantiated", __name__)

    def get_protocol(self) -> Protocol:
        """
        Get protocol runtime instance from persistant volume. If it is not available generate a new device
        instance from defaults.

        :return: protocol runtime object 
        :raises RuntimeError: if template is not loaded
        :rtype: Protocol
        """
        protocol = copy.deepcopy(sr.protocol)
        try:
            # read cached payload
            protocol_payload = self.read('protocol.json')
            protocol.setattrs(**protocol_payload)
        except (FileNotFoundError, JSONDecodeError) as exc:
            self._logger.warning("Failed to read protocol cache %s", exc)
        return protocol

    def get_imaging_profile(self) -> ImagingProfile:
        """
        Get imaging profile runtime instance from persistant volume. If it is not available generate a new device
        instance from defaults.

        :return: protocol runtime object 
        :raises RuntimeError: if template is not loaded
        :rtype: ImagingProfile
        """
        imaging_profile = copy.deepcopy(sr.imaging_profile)
        try:
            # read cached payload
            imaging_payload = self.read('imaging.json')
            imaging_profile.setattrs(**imaging_payload)
        except (FileNotFoundError, JSONDecodeError) as exc:
            self._logger.warning("Failed to read imaging profile cache %s", exc)
        return imaging_profile

    def get_experiment(self) -> Experiment:
        """
        Get experiment runtime instance from persistant volume if available. If it is not available generate a new
        experiment instance from defaults

        :return: experiment runtime object
        :raises RuntimeError: if template is not loaded
        :rtype: Experiment
        """
        experiment = copy.deepcopy(sr.experiment)
        try:
            # read cached payload
            experiment_payload = self.read('experiment.json')
            # migrate the payload for code version
            experiment.setattrs(**experiment_payload)
        except (FileNotFoundError, JSONDecodeError) as exc:
            self._logger.warning("Failed to read experiment cache %s", exc)
        else:
            # check for experiment expiry before dispatching with 5 second buffer
            if not experiment.initialized or datetime.now(timezone.utc).timestamp() + 5 > experiment.end_at.timestamp():
                # do not trigger any events if experiment expired while sleeping
                self.clear_thumbnail()
                self._logger.info("Cleared cache of expired experiment")
        return experiment

    def get_device(self) -> Device:
        """
        Get device runtime object from persistant volume. If it is not available generate a new device
        instance from defaults. Set the registration flag based on local filesystem contents

        :return: experiment runtime object
        :raises RuntimeError: if template is not loaded
        :rtype: Device
        """
        # set default registration status based on local lab_id file
        local_id = self.read_lab_id()
        device = copy.deepcopy(sr.device)
        try:
            # read cached payload
            device_payload = self.read('device.json')
            device.setattrs(**device_payload)
            # set lab_id (auto updates registration status)
            device.lab_id = local_id
        except (FileNotFoundError, JSONDecodeError) as exc:
            self._logger.warning("Failed to read device cache %s", exc)
            # load in device payload from default
            device.jwt = None
            device.jwt_payload = None
            # set lab_id (auto updates registration status)
            device.lab_id = local_id
            # cache default payload
            self.write(device)
        device.connected = False
        return device

    @staticmethod
    def write_device_avatar(img: bytes) -> None:
        """
        Write device avatar to disk

        :param img: [description]
        :type img: bytes
        """
        with ContextManager() as context:
            avatar_path = context.get_env('COMMON') + '/device_avatar.png'
            with open(avatar_path, 'wb') as avatar:
                avatar.write(img)

    @staticmethod
    def read_lab_id() -> Optional[int]:
        """
        Read cached lab id from disk

        :return: [description]
        :rtype: Optional[int]
        """
        with ContextManager() as context:
            try:
                with open(context.get_env('COMMON_CERTS') + '/lab_id.txt', 'r') as fp:
                    contents = fp.readlines()
            except FileNotFoundError:
                return None
        return int(context.parse_id(contents))

    @staticmethod
    def write_lab_id(lab_id: Optional[int]) -> None:
        """
        Writes lab_id to the local lab_id file (lab_id.txt)
        """
        with ContextManager() as context:
            if lab_id is None and os.path.isfile(context.get_env('COMMON_CERTS') + '/lab_id.txt'):
                os.remove(context.get_env('COMMON_CERTS') + '/lab_id.txt')
                return
            with open(context.get_env('COMMON_CERTS') + '/lab_id.txt', 'w+') as fp:
                fp.write(f"{lab_id}")

    @staticmethod
    def write(model: Union[ImagingProfile, Protocol, Experiment, Device]) -> None:
        """
        Save a runtime model to disk

        :param model: Runtime model to save to disk
        :type model: Union[ImagingProfile, Protocol, Experiment, Device]
        """
        if isinstance(model, ImagingProfile):
            filename = "imaging.json"
        elif isinstance(model, Protocol):
            filename = "protocol.json"
        elif isinstance(model, Experiment):
            filename = "experiment.json"
        else:
            filename = "device.json"
        with ContextManager() as context:
            filename = context.get_env('MONITOR_CACHE') + '/' + filename
            with open(filename, 'w+') as json_file:
                json.dump(model.getattrs(), json_file)

    @staticmethod
    def read(filename: str) -> dict:
        """
        Read json payload from cache

        :param filename: cache filename
        :type filename: str
        :return: dict document from cache
        :rtype: dict
        """
        with ContextManager() as context:
            filename = context.get_env('MONITOR_CACHE') + '/' + filename
            with open(filename, 'r') as json_file:
                payload: dict = json.load(json_file)
        return payload

    @staticmethod
    def clear(filename: str) -> None:
        """
        Clear cached runtime object artefacts

        :param filename: filename to remove 
        :type filename: str
        """
        with ContextManager() as context:
            filename = context.get_env('MONITOR_CACHE') + '/' + filename
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass

    @staticmethod
    def clear_thumbnail() -> None:
        """
        Remove thumbnail image from COMMON
        """
        # remove cached thumbnail image
        with ContextManager() as context:
            filename = context.get_env('COMMON') + "/thumbnail.png"
            try:
                os.remove(filename)
            except FileNotFoundError:
                pass

    @staticmethod
    def write_thumbnail(img: bytes) -> None:
        """
        Write experiment thumbnail to disk

        :param img: image payload in byte format
        :type img: bytes
        """
        with ContextManager() as context:
            thumbnail_path = context.get_env('COMMON') + '/thumbnail.png'
            with open(thumbnail_path, 'wb') as thumbnail:
                thumbnail.write(img)
