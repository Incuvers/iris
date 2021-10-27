#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ApiHandler
==========
Modified: 2021-05

This module is responsible for sending our various request types to our API and raising appropriate
exceptions that result from these requests. All outgoing raises are base exceptions of type:
ConnectionError, TimeoutError, and KeyError. Exceptions raised within this module are from the
requests.exceptions library.

Dependencies:
-------------
```
import json
import logging
import requests
from retry import retry
from monitor.environment.context_manager import ContextManager
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import json
import logging
import requests

from retry import retry
from monitor.environment.state_manager import StateManager
from monitor.environment.context_manager import ContextManager
from monitor.environment.thread_manager import ThreadManager as tm


class ApiHandler:

    GET_TIMEOUT = 15
    POST_TIMEOUT = 15
    PUT_TIMEOUT = 15

    """
    Class that processes the service requests related to obtaining our device information
    """

    def __init__(self):
        # bind logging to config file
        self._logger = logging.getLogger(__name__)
        # add a session object interfacing requests (enables context management)
        self.session = requests.Session()
        with ContextManager() as context:
            self.url = context.get_env('API_BASE_URL') + context.get_env('API_BASE_PATH')
            self._logger.info("Set api url to %s", self.url)
        self._logger.info("Instantiation successful.")

    @tm.lock(tm.api_lock)
    def _get_request(self, path: str, jwt: str = None) -> requests.Response:
        """
        Performs a GET request to API and fetches response from requests.Session.

        :param path: url path associated with the request endpoint

        :raises requests.exceptions.RequestException: if there was an ambiguous exception that 
            occurred while handling the request.
        :raises requests.exceptions.Timeout: if response fetch timed out this catches ReadTimeout and ConnectTimeout
        :raises requests.exceptions.URLRequired: if the URL is not valid.
        :raises requests.exceptions.TooManyRedirects: if the request involves too many redirects.
        :raises requests.exceptions.ConnectionError: if the response fetch failed due to a network error
        :raises requests.exceptions.HTTPError: if the response fetch has a status code that is not 200

        :return: Response: the response object which holds the payload from the api call
        """
        # build the endpoint url
        self._logger.info("Starting API GET request to: %s", str(self.url) + path)
        if jwt is None:
            self._logger.info("Unauthenticated API call initiated without jwt.")
            with self.session as session:
                response = session.get(str(self.url) + path, timeout=self.GET_TIMEOUT)
        else:
            self._logger.info("Authenticated API GET request initiated with jwt: %s", jwt)
            headers = {'Authorization': jwt}
            with self.session as session:
                response = session.get(str(self.url) + path,
                                       timeout=self.GET_TIMEOUT, headers=headers)
        # raise HTTPError corresponding to the status code error
        self._logger.info("Request Reponse Reason: %s", response.reason)
        # raise HTTPError corresponding to the status code error
        response.raise_for_status()
        return response

    @tm.lock(tm.api_lock)
    def _post_request(self, path: str, jwt: str, payload: dict, file_payload: bytes = None,
                      csrf: str = None) -> requests.Response:
        """
        Performs a POST request to the Incuvers API.

        :param path: url path associated with the request endpoint
        :param payload: POST payload of type python dict

        :raises requests.exceptions.RequestException: if there was an ambiguous exception that
            occurred while handling the request.
        :raises requests.exceptions.Timeout: if response fetch timed out this catches ReadTimeout and ConnectTimeout
        :raises requests.exceptions.URLRequired: if the URL is not valid.
        :raises requests.exceptions.TooManyRedirects: if the request involves too many redirects.
        :raises requests.exceptions.ConnectionError: if the response fetch failed due to a network error
        :raises requests.exceptions.HTTPError: if the response fetch has a status code that is not 200

        :return:
        """
        # get device jwt from state
        self._logger.info("Starting API POST request to: %s\nJWT: %s\nPayload: %s",
                          str(self.url) + path, jwt, payload)
        headers = {
            "Authorization": jwt,
            "x-csrf-token": csrf
        }
        with self.session as session:
            if file_payload is None:
                response = session.post(
                    str(self.url) + path,
                    json=payload,
                    timeout=self.POST_TIMEOUT,
                    headers=headers
                )
            else:  # Need to restructure the request a bit it a file is present
                # jsonify python dict object
                response = session.post(
                    str(self.url) + path,
                    data={"data": json.dumps(payload)},
                    files={'media': file_payload},
                    timeout=self.POST_TIMEOUT,
                    headers=headers
                )
        # raise HTTPError corresponding to the status code error
        self._logger.info("Request Reponse Reason: %s", response.reason)
        # raise HTTPError corresponding to the status code error
        response.raise_for_status()
        return response

    @tm.lock(tm.api_lock)
    def _get_image(self, pre_signed_url: str) -> bytes:
        """
        Makes a response call to the presigned url for a saved image.

        :raises requests.exceptions.RequestException: if there was an ambiguous exception that
            occurred while handling the request.
        :raises requests.exceptions.Timeout: if response fetch timed out this catches ReadTimeout and ConnectTimeout
        :raises requests.exceptions.URLRequired: if the URL is not valid.
        :raises requests.exceptions.TooManyRedirects: if the request involves too many redirects.
        :raises requests.exceptions.ConnectionError: if the response fetch failed due to a network error
        :raises requests.exceptions.HTTPError: if the response fetch has a status code that is not 200

        :return bytes: Image contents from passed url
        """
        with self.session as session:
            # custom presigned response endpoint for fetching the image
            response = session.get(pre_signed_url, timeout=self.GET_TIMEOUT, stream=True)
            response.raise_for_status()
        return response.content

    @retry(ReferenceError, tries=3, delay=2)
    def post_calibration_time(self, payload: dict) -> None:
        """
        Updates backend with last co2 calibration time

        :raises KeyError: if response does not contain pre_signed_url
        :raises ConnectionError ConnectionAbortedError: if response status code indicates failure

        :return: response object containing device avatar
        """
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        path = f'/devices/{device.id}/calibration_time'
        csrf = device.jwt_payload.get('csrf') if device.jwt_payload is not None else None
        # if jwt doesnt exist request a new jwt and retry with backoff for update
        if jwt is None:
            result = self.refresh_jwt()
            if result: raise ReferenceError
            else: raise ConnectionError
        try:
            response = self._post_request(path, jwt, payload, csrf=csrf)
        except requests.exceptions.RequestException as exc:
            self._logger.exception(
                "Failed performing the post request to update the last calibration time")
            raise ConnectionError from exc
        else:
            self._logger.info("Response Reason: %s", response.reason)

    @retry(TimeoutError, tries=3, delay=1, backoff=2)
    def request_session_token(self):
        """
        This method executes the api call to request a new JWT. Note the backoff parameter in the
        retry decorator represents the doubling time starting from the value specified by the delay
        parameter

        :raises TimeoutError: if jwt request timed out. Here we want to wait with a backoff and retry
        :raises ConnectionError: if api call failed to return response or returned with bad status code
        :raises KeyError: if the JSON decode fails
        """
        with StateManager() as state:
            device = state.device
        path = f'/devices/{device.id}/get_device_jwt'
        try:
            response = self._get_request(path)
        except requests.exceptions.Timeout as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise TimeoutError from exc
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            response = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Exception: %s during payload parse", type(exc).__name__)
            raise KeyError from exc
        if response['message']:
            self._logger.info("Request for new JWT successfully dispatched")
        else:
            self._logger.warning('ID is not valid, no jwt was generated')

    def refresh_jwt(self) -> bool:
        """ Refresh JWT for rerequest """
        try:
            # if request session token raises connection error it is caught by the caller
            # of this method call. For a timeout we have to catch and typecast to ConnectionError
            self.request_session_token()
        except (TimeoutError, KeyError):
            self._logger.exception(
                "While attempting to rerequest the session token the server timed out.")
            return False
        self._logger.info("Refreshed jwt for rerequest")
        return True

    @retry(ReferenceError, tries=5, delay=10)
    def get_registration_key(self) -> str:
        """
        Fetch a registration key for device_id from AWS

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: for updating jwt. caught by @retry decorator
        :raises KeyError: if the JSON decode fails 

        :return json: json from response object containing the registration key
        """
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        path = f'/devices/{device.id}/key'
        # if jwt doesnt exist request a new jwt and retry with backoff for update
        if jwt is None:
            result = self.refresh_jwt()
            if result: raise ReferenceError
            else: raise ConnectionError
        try:
            response = self._post_request(path, jwt, payload={})
        except requests.exceptions.HTTPError as exc:
            self._logger.exception("Exception: %s status_code: %s during fetch",
                                   type(exc).__name__,
                                   exc.response.status_code
                                   )
            if exc.response.status_code == 401:
                result = self.refresh_jwt()
                if result: raise ReferenceError
                else: raise ConnectionError
            elif exc.response.status_code == 404:
                # FIXME:if the url doesnt exist it means the backend says we are registered and hasnt provided
                # this url. However we will simply ignore this assumpion and assume this device is unregistered
                self._logger.warning(
                    "Backend has not provided key url since it believes this device is registered.")
                return str("ERROR")
            raise ConnectionError from exc
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            response = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Problem detected in the returned payload value: %s", exc)
            raise KeyError from exc
        reg_key = response['registration_key']
        self._logger.info("Retrieved registration key: %s", reg_key)
        return reg_key

    def get_device_avatar(self) -> bytes:
        """
        Fetches the device avatar from AWS. If the response yields an error we do not retry since we
        have a backup device avatar for this purpose.

        :raises KeyError: if the JSON decode fails 
        :raises ConnectionError ConnectionAbortedError: if response status code indicates failure

        :return: response object containing device avatar
        """
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        path = f'/devices/{device.id}/avatar'
        try:
            response = self._get_request(path, jwt)
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            payload: dict = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Problem detected in the returned payload value: %s", exc)
            raise KeyError from exc
        self._logger.info("Retrieved device avatar url: %s", payload.get('pre_signed_url'))
        try:
            img = self._get_image(payload.get('pre_signed_url', ''))
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during image fetch", type(exc).__name__)
            raise ConnectionError from exc
        return img

    def get_exp_thumbnail(self, exp_id: int) -> bytes:
        """
        Fetches the experiment thumbnail from AWS.

        :param exp_id: active experiment id
        :raises KeyError: if the JSON Decode fails
        :raises ConnectionError ConnectionAbortedError: if response status code indicates failure

        :return: response object containing experiment thumbnail
        """
        path = f'/experiments/{exp_id}/images/thumbnail'
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        try:
            response = self._get_request(path, jwt)
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            response = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Problem detected in the returned payload value: %s", exc)
            raise KeyError from exc
        if 'composite_path' in response:
            img_url = response['composite_path']
            self._logger.info("Retrieved composite thumbnail: %s", img_url)
        else:
            img_url = response['phase_path']
            self._logger.info("Retrieved dpc thumbnail: %s", img_url)
        try:
            img = self._get_image(img_url)
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during image fetch", type(exc).__name__)
            raise ConnectionError from exc
        return img

    @retry(ReferenceError, tries=2, delay=2)
    @retry(TimeoutError, tries=2, delay=2)
    def post_img(self, payload: dict, exp_id: int, file_payload: bytes) -> int:
        """
        Post DPC captures to AWS lambda for post-processing. The first image post is using image
        number 0 with the image payload. This creates a dpc image row in our table. This in turn
        returns an image ID for that image pack. Subsequent images (1,2,3) will be posted with the
        image pack ID field specified.

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: for updating jwt. caught by @retry decorator
        :raises KeyError: if the JSON decode fails

        :return int: image id
        """
        path = f'/experiments/{exp_id}/images'
        response = None
        # validate jwt before request
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        csrf = device.jwt_payload.get('csrf') if device.jwt_payload is not None else None
        # if jwt doesnt exist request a new jwt and retry with backoff for update
        if jwt is None:
            result = self.refresh_jwt()
            if result: raise ReferenceError
            else: raise ConnectionError
        try:
            response = self._post_request(
                path, jwt, payload, file_payload, csrf)
        except requests.exceptions.HTTPError as exc:
            self._logger.exception("Exception: %s status_code: %s during fetch",
                                   type(exc).__name__,
                                   exc.response.status_code
                                   )
            # reattempt if the server gives a bad 400 response which does not involve a bad url
            if exc.response.status_code == 401:
                result = self.refresh_jwt()
                if result: raise ReferenceError
            raise ConnectionError from exc
        except requests.exceptions.Timeout as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise TimeoutError from exc
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            response_payload: dict = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Exception: %s during payload parse", type(exc).__name__)
            raise KeyError from exc
        image_id = response_payload['image_id']
        self._logger.info("Retrieved image id: %s", image_id)
        return image_id

    @retry(ReferenceError, tries=2, delay=2)
    @retry(TimeoutError, tries=2, delay=2)
    def post_preview(self, payload: dict, file_payload: bytes) -> None:
        """
        Post DPC captures to AWS lambda for post-processing. The first image post is using image
        number 0 with the image payload. This creates a dpc image row in our table. This in turn
        returns an image ID for that image pack. Subsequent images (1,2,3) will be posted with the
        image pack ID field specified.

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: for updating jwt. caught by @retry decorator
        :raises KeyError: if the 'registration_key' key does not exist in the returned response
        """
        with StateManager() as state:
            device = state.device
        path = f'/preview/{device.id}'
        # validate jwt before request
        jwt = device.jwt
        csrf = device.jwt_payload.get('csrf') if device.jwt_payload is not None else None
        # validate jwt before request
        if jwt is None:
            result = self.refresh_jwt()
            if result: raise ReferenceError
            else: raise ConnectionError
        try:
            _ = self._post_request(path, jwt, payload, file_payload, csrf)
        except requests.exceptions.HTTPError as exc:
            self._logger.exception("Exception: %s status_code: %s during fetch",
                                   type(exc).__name__,
                                   exc.response.status_code
                                   )
            # reattempt if the server gives a bad 400 response which does not involve a bad url
            if exc.response.status_code == 401:
                result = self.refresh_jwt()
                if result: raise ReferenceError
            raise ConnectionError from exc
        except requests.exceptions.Timeout as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise TimeoutError from exc
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc

    @retry(ReferenceError, tries=2, delay=2)
    def get_device_info(self) -> dict:
        """
        Fetch the device info from AWS

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: for updating jwt. caught by @retry decorator

        :return dict: json from response object containing the device info
        """
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        path = f'/devices/{device.id}'
        try:
            response = self._get_request(path, jwt)
        except requests.exceptions.HTTPError as exc:
            self._logger.exception("Exception: %s status_code: %s during fetch",
                                   type(exc).__name__,
                                   exc.response.status_code
                                   )
            if exc.response.status_code == 401:
                result = self.refresh_jwt()
                if result: raise ReferenceError
            raise ConnectionError from exc
        except requests.exceptions.RequestException as exc:
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            response = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Exception: %s during payload parse", type(exc).__name__)
            raise KeyError from exc
        self._logger.info("Retrieved device info: %s", response)
        return response

    @retry(ReferenceError, tries=2, delay=2)
    def get_experiment(self) -> dict:
        """
        Fetch the new experiment for this device

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: for updating jwt. caught by @retry decorator

        :return json: json from response object containing the experiment
        """
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        path = f'/devices/{device.id}/pending_experiment'
        try:
            response = self._get_request(path, jwt)
        except requests.exceptions.HTTPError as exc:
            self._logger.exception("Exception: %s status_code: %s during fetch",
                                   type(exc).__name__,
                                   exc.response.status_code
                                   )
            if exc.response.status_code == 401:
                result = self.refresh_jwt()
                if result: raise ReferenceError
                else: raise ConnectionError
            raise ConnectionError from exc
        except requests.exceptions.RequestException as exc:  # request base exception
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            response = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Exception: %s during payload parse", type(exc).__name__)
            raise KeyError from exc
        self._logger.info("Retrieved experiment: %s", response)
        return response

    @retry(ReferenceError, tries=2, delay=2)
    def get_imaging_profile(self, imaging_profile_id: int) -> dict:
        """
        Fetch the imaging profile for an experiment

        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: for updating jwt. caught by @retry decorator

        :return json: json from response object containing the imaging profile payload
        """
        path = f'/imaging_profiles/{imaging_profile_id}'
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        try:
            response = self._get_request(path, jwt)
        except requests.exceptions.HTTPError as exc:
            self._logger.exception("Exception: %s status_code: %s during fetch",
                                   type(exc).__name__,
                                   exc.response.status_code
                                   )
            if exc.response.status_code == 401:
                result = self.refresh_jwt()
                if result: raise ReferenceError
                else: raise ConnectionError
            raise ConnectionError from exc
        except requests.exceptions.RequestException as exc:  # request base exception
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            response = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Exception: %s during payload parse", type(exc).__name__)
            raise KeyError from exc
        self._logger.info("Retrieved imaging profile: %s", response)
        return response

    @retry(ReferenceError, tries=2, delay=2)
    def get_protocol(self, protocol_id: int) -> dict:
        """
        Fetch the new protocol for this device

        :raises KeyError: if the response payload failed to parse
        :raises ConnectionError: if the response is not fetched due to a connection error or timeout
        :raises ReferenceError: for updating jwt. caught by @retry decorator

        :return json: json from response object containing the protocol
        """
        path = f'/protocols/{protocol_id}'
        with StateManager() as state:
            device = state.device
        jwt = device.jwt
        try:
            response = self._get_request(path, jwt)
        except requests.exceptions.HTTPError as exc:
            self._logger.exception("Exception: %s status_code: %s during fetch",
                                   type(exc).__name__,
                                   exc.response.status_code
                                   )
            if exc.response.status_code == 401:
                result = self.refresh_jwt()
                if result: raise ReferenceError
                else: raise ConnectionError
            raise ConnectionError from exc
        except requests.exceptions.RequestException as exc:  # request base exception
            self._logger.exception("Exception: %s during fetch", type(exc).__name__)
            raise ConnectionError from exc
        try:
            response = response.json()
        except json.decoder.JSONDecodeError as exc:
            self._logger.exception("Exception: %s during payload parse", type(exc).__name__)
            raise KeyError from exc
        self._logger.info("Retrieved protocol: %s", response)
        return response
