# -*- coding: utf-8 -*-
"""
API Proxy
=========
Modified: 2021-06

Dependencies:
-------------
```
import logging
from monitor.sys import decorators
from monitor.imaging.capture import Capture
from monitor.cloud.api_handler import ApiHandler
from monitor.models.experiment import Experiment
from monitor.events.event_handler import EventHandler
from monitor.environment.context_manager import ContextManager
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
from datetime import datetime
import logging

from monitor.sys.decorators import cache
from monitor.api.cache import ProxyCache
from monitor.imaging.capture import Capture
from monitor.api.api_handler import ApiHandler
from monitor.environment.state_manager import StateManager
from monitor.events.registry import Registry as events


class ApiProxy:

    def __init__(self):
        # register logger with module name
        self._logger = logging.getLogger(__name__)
        self._api_handler = ApiHandler()
        self.cache = ProxyCache()
        # stage pipeline execution sequences
        events.preview_pipeline.stage(self.upload_preview, 1)
        events.thumbnail_pipeline.stage(self.get_thumbnail, 0)
        events.registration_pipeline.stage(self.get_device_registration_key, 1)
        # event registration
        events.capture_pipeline.stage(self.upload_images, 2)
        events.new_protocol.register(self.get_protocol)
        events.new_device.register(self.get_device_info_and_avatar)
        events.new_experiment.register(self.get_experiment)
        events.renew_jwt.register(self.request_jwt)
        self._logger.info("Instantiation successful.")

    def request_jwt(self) -> None:
        """
        Manually invoked once on system startup as it connects to the cloud.
        """
        try:
            self._api_handler.request_session_token()
        except (TimeoutError, ConnectionError, KeyError) as exc:
            self._logger.warning("Could not retrieve jwt: %s", exc)
        else:
            # if we get here it means the session token request was successful. This indicates that the
            # connection to the api is re-established and we can now execute cached requests
            self.cache.execute()

    def get_device_registration_key(self) -> str:
        """
        Get registration key fromm backend

        :return: registration key string 
        :rtype: str
        """
        registration_key = self._api_handler.get_registration_key()
        self._logger.info("Fetched device registration key: %s", registration_key)
        return registration_key

    @cache
    def get_thumbnail(self) -> None:
        """
        Get the experiment thumbnail from the api
        """
        # experiment guard
        with StateManager() as state:
            experiment = state.experiment
        if experiment.active:
            response = self._api_handler.get_exp_thumbnail(experiment.id)
            events.cache_thumbnail.trigger(response)

    @cache
    def get_device_info_and_avatar(self) -> None:
        """
        Retrieves device info and avatar metadata from the api and saves them locally.

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: the jwt was requested on a 401 not be updated locally in time for
        the request to be completed
        """
        device_payload = self._api_handler.get_device_info()
        try:
            response = self._api_handler.get_device_avatar()
        except KeyError:
            self._logger.warning("No device avatar set.")
        else:
            events.avatar_pipeline.begin(response)
        with StateManager() as state:
            device = state.device
            device.setattrs(**device_payload)
            state.commit(device)

    @cache
    def get_protocol(self, protocol_id: int) -> None:
        """
        Retrieves a specific protocol from api and applies the it to the system

        :param protocol_id: id of the protocol to be fetched.
        """
        protocol_payload = self._api_handler.get_protocol(protocol_id)
        with StateManager() as state:
            protocol = state.protocol
            protocol.setattrs(**protocol_payload)
            state.commit(protocol)

    @cache
    def get_experiment(self) -> None:
        """
        Retrieves the pending experiment from api then uses the linked imaging_profile_id and
        protocol_id to make another request to get the imaging_profile. Once all 3 payloads are
        obtained we update the system. This function is cache compliant (i.e. reversible)

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: the jwt was requested on a 401 not be updated locally in time for
        the request to be completed
        """
        # api request
        experiment_payload = self._api_handler.get_experiment()
        if experiment_payload != "None":
            self._logger.debug("Fetched experiment payload: %s", experiment_payload)
            # commit the experiment state first so setpoint scheduler can reference experiment start time
            # and validate experiment and protocol id match
            with StateManager() as state:
                experiment = state.experiment
                experiment.setattrs(**experiment_payload)
                state.commit(experiment)
            # protocol resolution
            protocol_id = experiment_payload['protocol_id']
            self.get_protocol(protocol_id)
            # get the imaging profile requested by the experiment payload
            imaging_profile_id = experiment_payload['imaging_profile_id']
            self.get_imaging_profile(imaging_profile_id)
        else:
            # if the payload is None then we manually set the stop_at to the current time and update the system
            with StateManager() as state:
                experiment = state.experiment
                # set the stop_at to now
                experiment.stop_at = datetime.utcnow()
                state.commit(experiment)

    @cache
    def get_imaging_profile(self, imaging_profile_id: int) -> None:
        """
        Retrieves an imaging profile from the api. This function we do not cache since it is part of
        the experiment pipeline execution sequence and api failures will be caught by the get_experiment() call

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: the jwt was requested on a 401 not be updated locally in time for
        the request to be completed
        :return: imaging profile payload from api
        """
        # api request
        imaging_profile_payload = self._api_handler.get_imaging_profile(imaging_profile_id)
        # trigger external events
        self._logger.debug("Fetched imaging profile payload: %s", imaging_profile_payload)
        with StateManager() as state:
            imaging_profile = state.imaging_profile
            imaging_profile.setattrs(**imaging_profile_payload)
            result = state.commit(imaging_profile)
            if not result: self._logger.error("Inbound imaging profile failed ISV checks")
            else: self._logger.info("Inbound imaging profile successfully commited to the system")

    @cache
    def upload_images(self, capture: Capture, image_id: int = None, index: int = 0) -> None:
        """
        Post captures to AWS lambda for post-processing. The first image post is using image
        number 0 with the image payload. This creates a dpc image row in our table. This in turn
        returns an image ID for that image pack. Subsequent images (1,2,3) will be posted with the
        image pack ID field specified. The capture object may include an optional 5th GFP capture.

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: the jwt was requested on a 401 not be updated locally in time for
        the request to be completed
        """
        with StateManager() as state:
            exp_id = state.experiment.id
        file_payload = capture.get_processed(index=index)
        # json cannot be serialized with raw bytes so we decode it to a utf-8 string
        # build payload using current index as a key generator
        payload = {
            'type': 'DPC_{}'.format(index) if index != 4 else 'GFP',
            'image_id': image_id if index != 0 else None,
        }
        self._logger.debug("Generated payload %s", payload)
        # api request
        image_id = self._api_handler.post_img(payload, exp_id, file_payload)
        # recurse until all images are uploaded
        if (index < len(capture.captures) - 1):
            self.upload_images(capture, image_id=image_id, index=index + 1)

    @cache
    def upload_preview(self, capture: Capture, index: int = 0) -> None:
        """
        Post preview captures to AWS S3 for post-processing. The first image post is using image
        number 0 with the image payload. This creates a dpc image row in our table. This in turn
        returns an image ID for that image pack. Subsequent images (1,2,3) will be posted with the
        image pack ID field specified.

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: the jwt was requested on a 401 not be updated locally in time for
        the request to be completed
        """
        events.cloud_sync.trigger(True)
        file_payload = capture.get_processed(index=index)
        payload = {
            'type': 'DPC_{}'.format(index) if index != 4 else 'GFP',
            'is_gfp': capture.gfp_capture
        }
        self._logger.debug("Generated payload %s", payload)
        # api request
        self._api_handler.post_preview(payload, file_payload)
        # recurse until all images are uploaded
        if (index < len(capture.captures) - 1):
            self.upload_preview(capture, index + 1)
        events.cloud_sync.trigger(False)

    @cache
    def send_co2_calibration_time(self, calibration_time: str) -> None:
        """
        Send last calibrated CO2 time to the backend for display on the front end

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: the jwt was requested on a 401 not be updated locally in time for
        the request to be completed
        """
        payload = {
            'iso_date': calibration_time
        }
        self._api_handler.post_calibration_time(payload)

    @staticmethod
    def migrate(reference: dict, digest: dict, _logger: logging.Logger) -> dict:
        """
        Migration must apply 2 operations to any incoming payload from both the 
        backend api and the system cache:
         1. Addition of new payload fields
         2. Subtraction of payload fields which no longer apply
        NOTE: this migration code only supports delta detection @ the first json layer and does not inspect for changes
        beyond the first layer

        :param reference: dict reference payload for building migration filter
        :type reference: dict
        :param digest: dict incoming payload for migration filtering
        :type digest: dict
        :return: outgoing payload after migration filtering
        :rtype: dict
        """
        # ensure outgoing payload inherits all fields from template (baseline)
        ref = reference.copy()
        # apply key addition and filtering
        for key, value in digest.items():
            if key in ref.keys():
                # add key if not present in template
                ref[key] = value
            else:
                _logger.warning(
                    "Migration warning | key : '%s' is not supported on this version of the codebase.", key)
        _logger.debug("Applied payload migration with outgoing digest: %s", reference)
        return ref
