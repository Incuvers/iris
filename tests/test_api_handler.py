# -*- coding: utf-8 -*-
"""
Unittest for ApiHandler
=======================
Date: 2021-04

Dependencies:
-------------
```
import requests
import unittest
from json.decoder import JSONDecodeError
from monitor.tests import resources
from unittest.mock import Mock, patch
from monitor.cloud.api_handler import ApiHandler
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

# flake8: noqa
import json
import logging
import requests
import unittest
from unittest.mock import MagicMock, Mock, patch
patch('retry.retry', lambda *x, **y: lambda f: f).start()  # noqa
from json.decoder import JSONDecodeError
from monitor.api.api_handler import ApiHandler
from monitor.environment.thread_manager import ThreadManager
from monitor.environment.state_manager import StateManager
from monitor.models.device import Device
from tests.resources import backend


class TestApiHandler(unittest.TestCase):

    false_path = '/v1/devices/1234/get_key'
    false_pre_signed_url = ''
    request_exc = {
        'ConnectionError': requests.exceptions.ConnectionError,
        'URLRequired': requests.exceptions.URLRequired,
        'Timeout': requests.exceptions.Timeout,
        'RequestException': requests.exceptions.RequestException,
        'TooManyRedirects': requests.exceptions.TooManyRedirects,
        'HTTPError': requests.exceptions.HTTPError
    }

    def setUp(self):
        logging.disable()
        self.api_handler = ApiHandler(base_url='localhost', base_path='/v1')

    def tearDown(self):
        del self.api_handler
        logging.disable(logging.NOTSET)

    @patch.object(ThreadManager, 'lock')
    @patch("requests.Session.get")
    def test_get_request(self, get: MagicMock, _: MagicMock):
        """
        Test api get request helper method

        :param get: mocked session.get method
        :type get: MagicMock
        """
        self.api_handler.url = "test"
        self.api_handler._get_request(self.false_path)
        get.assert_called_once_with(self.api_handler.url + self.false_path,
                                    timeout=self.api_handler.GET_TIMEOUT)
        get.reset_mock()
        # write dummy jwt to test authenticated calls
        self.api_handler._get_request(self.false_path, backend.SAMPLE_JWT)
        get.assert_called_once_with(self.api_handler.url + self.false_path,
                                    timeout=self.api_handler.GET_TIMEOUT,
                                    headers={'Authorization': backend.SAMPLE_JWT})

    @patch.object(ThreadManager, 'lock')
    @patch("requests.Session.post")
    def test_post_request(self, post: MagicMock, _: MagicMock):
        """
        Test api post request helper method

        :param post: mocked session.post method 
        :type post: MagicMock
        """
        self.api_handler.url = "test"
        self.api_handler._post_request(
            self.false_path, backend.SAMPLE_JWT, backend.SAMPLE_POST_PAYLOAD)
        header = {'Authorization': backend.SAMPLE_JWT, "x-csrf-token": None}
        post.assert_called_once_with(self.api_handler.url + self.false_path,
                                     json=backend.SAMPLE_POST_PAYLOAD,
                                     timeout=self.api_handler.POST_TIMEOUT,
                                     headers=header)
        post.reset_mock()
        # write dummy jwt to test authenticated calls
        self.api_handler._post_request(
            self.false_path, backend.SAMPLE_JWT, backend.SAMPLE_POST_PAYLOAD, bytes(10))
        post.assert_called_once_with(self.api_handler.url + self.false_path,
                                     data={"data": json.dumps(backend.SAMPLE_POST_PAYLOAD)},
                                     files={"media": bytes(10)},
                                     timeout=self.api_handler.POST_TIMEOUT,
                                     headers=header)

    @patch.object(ApiHandler, '_post_request', autospec=True)
    @patch.object(ApiHandler, 'refresh_jwt', autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_post_calibration_time(self, state: MagicMock, refresh_jwt: MagicMock, post: MagicMock):
        """
        Test calibration post method and exceptions

        :param state: mocked state manager
        :type state: MagicMock
        :param refresh_jwt: mocked refresh jwt
        :type refresh_jwt: MagicMock
        :param post: mocked post method
        :type post: MagicMock
        """
        state.return_value.device = mock_device = Mock(spec=Device)
        # test no jwt in state model
        mock_device.jwt = None
        mock_device.jwt_payload = None
        # test successful refresh
        refresh_jwt.return_value = True
        with self.assertRaises(ReferenceError):
            self.api_handler.post_calibration_time(payload={'sample': "test"})
        # test failed refresh
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.post_calibration_time(payload={'sample': "test"})
        # test sanity
        mock_device.jwt = backend.SAMPLE_JWT
        mock_device.jwt_payload = backend.SAMPLE_JWT_PAYLOAD
        self.api_handler.post_calibration_time(payload={'sample': "test"})
        post.assert_called_once()
        # test api post exceptions
        for key, exc in self.request_exc.items():
            with self.subTest("_post_request() exception: {}".format(key)):
                post.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.post_calibration_time(payload={'sample': "test"})

    @patch.object(ApiHandler, '_post_request', autospec=True)
    @patch.object(ApiHandler, 'refresh_jwt', autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_post_img(self, state: MagicMock, refresh_jwt: MagicMock, post: MagicMock):
        """
        Test image posting method and exception handling

        :param state: mocked state manager 
        :type state: MagicMock
        :param refresh_jwt: mocked refresh_jwt method
        :type refresh_jwt: MagicMock
        :param post: mocked api post method
        :type post: MagicMock
        """
        state.return_value.device = mock_device = Mock(spec=Device)
        # test sanity
        mock_device.jwt = backend.SAMPLE_JWT
        mock_device.jwt_payload = backend.SAMPLE_JWT_PAYLOAD
        self.api_handler.post_img({'sample': "test"}, 4, bytes(10))
        post.assert_called_once()
        # test no jwt in state model
        mock_device.jwt = None
        mock_device.jwt_payload = None
        # test successful refresh
        refresh_jwt.return_value = True
        with self.assertRaises(ReferenceError):
            self.api_handler.post_img({'sample': "test"}, 4, bytes(10))
        # test failed refresh
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.post_img({'sample': "test"}, 4, bytes(10))
        # test post connection exceptions
        mock_device.jwt = backend.SAMPLE_JWT
        mock_device.jwt_payload = backend.SAMPLE_JWT_PAYLOAD
        timeout = self.request_exc.pop('Timeout')
        http = self.request_exc.pop('HTTPError')
        for key, exc in self.request_exc.items():
            with self.subTest("_post_request exception: {}".format(key)):
                post.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.post_img({'sample': "test"}, 4, bytes(10))
        self.request_exc['Timeout'] = timeout
        self.request_exc['HTTPError'] = http
        # test successful jwt rerequest
        mock_err = Mock().return_value = requests.Response()
        mock_err.status_code = 401
        post.side_effect = requests.exceptions.HTTPError(response=mock_err)
        refresh_jwt.return_value = True
        with self.assertRaises(ReferenceError):
            self.api_handler.post_img({'sample': "test"}, 4, bytes(10))
        # test unsuccessful jwt rerequest
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.post_img({'sample': "test"}, 4, bytes(10))
        # test bad http status code
        mock_err.status_code = 500
        post.side_effect = requests.exceptions.HTTPError(response=mock_err)
        with self.assertRaises(ConnectionError):
            self.api_handler.post_img({'sample': "test"}, 4, bytes(10))
        # test timeout error
        post.side_effect = self.request_exc['Timeout']
        with self.assertRaises(TimeoutError):
            self.api_handler.post_img({'sample': "test"}, 4, bytes(10))
        # create test JSON decode error exception and inject into response.json() call
        post.side_effect = None
        post.return_value.json.side_effect = JSONDecodeError("test", "docstring", 10)
        with self.assertRaises(KeyError):
            self.api_handler.post_img({'sample': "test"}, 4, bytes(10))

    @patch.object(ApiHandler, '_get_request', autospec=True)
    @patch.object(ApiHandler, 'refresh_jwt', autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_imaging_profile(self, _: MagicMock, refresh_jwt: MagicMock, get: MagicMock):
        """
        Test imaging profile get method and exception handling

        :param state: mocked state manager 
        :type state: MagicMock
        :param refresh_jwt: mocked method 
        :type refresh_jwt: MagicMock
        :param get: mocked api get helper method 
        :type get: MagicMock
        """
        # test sanity
        self.api_handler.get_imaging_profile(1)
        get.assert_called_once()
        # create a mock HTTPError with a response.status_code of 401
        refresh_jwt.return_value = True
        mock_err = Mock().return_value = requests.Response()
        mock_err.status_code = 401
        get.side_effect = requests.exceptions.HTTPError(response=mock_err)
        with self.assertRaises(ReferenceError):
            self.api_handler.get_imaging_profile(1)
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.get_imaging_profile(1)
        # test connection error raise on 400
        refresh_jwt.reset_mock()
        mock_err.status_code = 400
        with self.assertRaises(ConnectionError):
            self.api_handler.get_imaging_profile(1)
        refresh_jwt.assert_not_called()
        # test general request exceptions
        http = self.request_exc.pop('HTTPError')
        timeout = self.request_exc.pop('Timeout')
        for key, exc in self.request_exc.items():
            with self.subTest("_get_request exception: {}".format(key)):
                get.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_imaging_profile(1)
        self.request_exc['Timeout'] = timeout
        self.request_exc['HTTPError'] = http
        # test json decode exception
        get.side_effect = None
        get.return_value.json = Mock(side_effect=JSONDecodeError("test", "docstring", 10))
        with self.assertRaises(KeyError):
            self.api_handler.get_imaging_profile(1)

    @patch.object(ApiHandler, '_get_request', autospec=True)
    @patch.object(ApiHandler, 'refresh_jwt', autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_protocol(self, _: MagicMock, refresh_jwt: MagicMock, get: MagicMock):
        """
        Test protocol get method and exception handling

        :param state: mocked state manager 
        :type state: MagicMock
        :param refresh_jwt: mocked method 
        :type refresh_jwt: MagicMock
        :param get: mocked api get helper method 
        :type get: MagicMock
        """
        # test sanity
        self.api_handler.get_protocol(1)
        get.assert_called_once()
        # create a mock HTTPError with a response.status_code of 401
        refresh_jwt.return_value = True
        mock_err = Mock().return_value = requests.Response()
        mock_err.status_code = 401
        get.side_effect = requests.exceptions.HTTPError(response=mock_err)
        with self.assertRaises(ReferenceError):
            self.api_handler.get_protocol(1)
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.get_protocol(1)
        # test connection error raise on 400
        refresh_jwt.reset_mock()
        mock_err.status_code = 400
        with self.assertRaises(ConnectionError):
            self.api_handler.get_protocol(1)
        refresh_jwt.assert_not_called()
        # test general request exceptions
        http = self.request_exc.pop('HTTPError')
        timeout = self.request_exc.pop('Timeout')
        for key, exc in self.request_exc.items():
            with self.subTest("_get_request exception: {}".format(key)):
                get.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_protocol(1)
        self.request_exc['Timeout'] = timeout
        self.request_exc['HTTPError'] = http
        # test json decode exception
        get.side_effect = None
        get.return_value.json = Mock(side_effect=JSONDecodeError("test", "docstring", 10))
        with self.assertRaises(KeyError):
            self.api_handler.get_protocol(1)

    @patch.object(ApiHandler, '_get_request', autospec=True)
    @patch.object(ApiHandler, 'refresh_jwt', autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_experiment(self, _: MagicMock, refresh_jwt: MagicMock, get: MagicMock):
        """
        Test experiment get method and exception handling

        :param state: mocked state manager 
        :type state: MagicMock
        :param refresh_jwt: mocked method 
        :type refresh_jwt: MagicMock
        :param get: mocked api get helper method 
        :type get: MagicMock
        """
        # test sanity
        self.api_handler.get_experiment()
        get.assert_called_once()
        # create a mock HTTPError with a response.status_code of 401
        refresh_jwt.return_value = True
        mock_err = Mock().return_value = requests.Response()
        mock_err.status_code = 401
        get.side_effect = requests.exceptions.HTTPError(response=mock_err)
        with self.assertRaises(ReferenceError):
            self.api_handler.get_experiment()
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.get_experiment()
        # test connection error raise on 400
        refresh_jwt.reset_mock()
        mock_err.status_code = 400
        with self.assertRaises(ConnectionError):
            self.api_handler.get_experiment()
        refresh_jwt.assert_not_called()
        # test general request exceptions
        http = self.request_exc.pop('HTTPError')
        timeout = self.request_exc.pop('Timeout')
        for key, exc in self.request_exc.items():
            with self.subTest("_get_request exception: {}".format(key)):
                get.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_experiment()
        self.request_exc['Timeout'] = timeout
        self.request_exc['HTTPError'] = http
        # test json decode exception
        get.side_effect = None
        get.return_value.json = Mock(side_effect=JSONDecodeError("test", "docstring", 10))
        with self.assertRaises(KeyError):
            self.api_handler.get_experiment()

    @patch.object(ApiHandler, '_post_request', autospec=True)
    @patch.object(ApiHandler, 'refresh_jwt', autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_post_preview(self, state: MagicMock, refresh_jwt: MagicMock, post: MagicMock):
        """
        Test post preview method and exception handling

        :param state: mocked state manager 
        :type state: MagicMock
        :param refresh_jwt: mocked refresh_jwt method 
        :type refresh_jwt: MagicMock
        :param post: mocked api post method
        :type post: MagicMock
        """
        state.return_value.device = mock_device = Mock(spec=Device)
        # test no jwt in state model
        mock_device.jwt = None
        mock_device.jwt_payload = None
        # test successful refresh
        refresh_jwt.return_value = True
        with self.assertRaises(ReferenceError):
            self.api_handler.post_preview({'sample': "test"}, bytes(10))
        # test failed refresh
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.post_preview({'sample': "test"}, bytes(10))
        # test sanity
        mock_device.jwt = backend.SAMPLE_JWT
        mock_device.jwt_payload = backend.SAMPLE_JWT_PAYLOAD
        self.api_handler.post_preview({'sample': "test"}, bytes(10))
        post.assert_called_once()
        # create a mock HTTPError with a response.status_code of 401
        mock_err = Mock().return_value = requests.Response()
        mock_err.status_code = 401
        post.side_effect = requests.exceptions.HTTPError(response=mock_err)
        # test successful refresh
        refresh_jwt.return_value = True
        with self.assertRaises(ReferenceError):
            self.api_handler.post_preview({'sample': "test"}, bytes(10))
        # test failed refresh
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.post_preview({'sample': "test"}, bytes(10))
        # test connection error raise on 400
        mock_err.status_code = 400
        with self.assertRaises(ConnectionError):
            self.api_handler.post_preview(payload={}, file_payload=bytes(10))
        # test general request exceptions
        http = self.request_exc.pop('HTTPError')
        timeout = self.request_exc.pop('Timeout')
        for key, exc in self.request_exc.items():
            with self.subTest("_post_request exception: {}".format(key)):
                post.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.post_preview(payload={}, file_payload=bytes(10))
        self.request_exc['Timeout'] = timeout
        self.request_exc['HTTPError'] = http
        # test timeout error handling
        post.reset_mock()
        post.side_effect = self.request_exc['Timeout']
        with self.assertRaises(TimeoutError):
            self.api_handler.post_preview(payload={}, file_payload=bytes(10))

    @patch('requests.Session.get')
    def test_get_image(self, get: MagicMock):
        """
        Test get image helper

        :param get: mocked session.get method
        :type get: MagicMock
        """
        # test success
        self.api_handler._get_image(self.false_pre_signed_url)
        get.assert_called_once()

    @patch.object(ApiHandler, '_get_request', autospec=True)
    @patch.object(ApiHandler, '_get_image', **{'return_value': bytes(10)}, autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_exp_thumbnail(self, _: MagicMock, get_img: MagicMock, get: MagicMock):
        """
        Test experiment thumbnail get helper and exception handling

        :param state: mocked state manager 
        :type state: MagicMock
        :param get_img: mocked image get helper method 
        :type get_img: MagicMock
        :param get: mocked api get helper method 
        :type get: MagicMock
        """
        # test sanity
        self.api_handler.get_exp_thumbnail(-1)
        get.assert_called_once()
        get_img.assert_called_once()
        # test composite path
        get.return_value.json.return_value = {'composite_path': "fake_url"}
        self.api_handler.get_exp_thumbnail(-1)
        # test bad decode
        get.return_value.json.side_effect = JSONDecodeError("test", "docstring", 10)
        with self.assertRaises(KeyError):
            self.api_handler.get_exp_thumbnail(-1)
        get.return_value.json.side_effect = None
        # test get exceptions
        for key, exc in self.request_exc.items():
            with self.subTest("_get_request exception: {}".format(key)):
                get.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_exp_thumbnail(-1)
        get.side_effect = None
        # test img get exceptions
        for key, exc in self.request_exc.items():
            with self.subTest("get_img exception: {}".format(key)):
                get_img.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_exp_thumbnail(-1)

    @patch.object(ApiHandler, '_get_request', autospec=True)
    @patch.object(ApiHandler, '_get_image', **{'return_value': Mock()})
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_device_avatar(self, _: MagicMock, get_img: MagicMock, get: MagicMock):
        """
        Test device avatar get method and exception handling

        :param state: mocked state manager 
        :type state: MagicMock
        :param get_img: mocked image get helper method 
        :type get_img: MagicMock
        :param get: mocked api get helper method 
        :type get: MagicMock
        """
        # test sanity
        self.api_handler.get_device_avatar()
        get.assert_called_once()
        get_img.assert_called_once()
        # Simulate all exception raises for using get request helper
        for key, exc in self.request_exc.items():
            with self.subTest("_get_request exception: {}".format(key)):
                get.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_device_avatar()
        get.side_effect = None
        # Simulate presigned url not in the payload and check for expected raise
        get.return_value.json.side_effect = JSONDecodeError("test", "docstring", 10)
        with self.assertRaises(KeyError):
            self.api_handler.get_device_avatar()
        get.return_value.json.side_effect = None
        # Simulate all exception raises for retriveing image using a presigned url
        for key, exc in self.request_exc.items():
            with self.subTest("get_img exception: {}".format(key)):
                get_img.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_device_avatar()

    @patch.object(ApiHandler, '_get_request', autospec=True)
    @patch.object(ApiHandler, 'refresh_jwt', autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_device_info(self, _: MagicMock, refresh_jwt: MagicMock, get: MagicMock):
        """
        Test device info get helper method and exception handling

        :param state: mocked state manager 
        :type state: MagicMock
        :param refresh_jwt: mocked method 
        :type refresh_jwt: MagicMock
        :param get: mocked api get helper method 
        :type get: MagicMock
        """
        # test sanity
        self.api_handler.get_device_info()
        get.assert_called_once()
        # simulate 401 retry
        refresh_jwt.return_value = True
        mock_err = Mock().return_value = requests.Response()
        mock_err.status_code = 401
        get.side_effect = requests.exceptions.HTTPError(response=mock_err)
        with self.assertRaises(ReferenceError):
            self.api_handler.get_device_info()
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.get_device_info()
        # test bad status code
        refresh_jwt.reset_mock()
        mock_err.status_code = 404
        get.side_effect = requests.exceptions.HTTPError(response=mock_err)
        with self.assertRaises(ConnectionError):
            self.api_handler.get_device_info()
        refresh_jwt.assert_not_called()
        # Simulate json decode error
        get.side_effect = None
        get.return_value.json = Mock(side_effect=JSONDecodeError("test", "docstring", 10))
        with self.assertRaises(KeyError):
            self.api_handler.get_device_info()
        # remove http error for this test case
        http_error = self.request_exc.pop('HTTPError')
        for key, exc in self.request_exc.items():
            with self.subTest("_get_request exception: {}".format(key)):
                get.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_device_info()
        self.request_exc['HTTPError'] = http_error

    @patch.object(ApiHandler, '_post_request', autospec=True)
    @patch.object(ApiHandler, 'refresh_jwt', autospec=True)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_registration_key(self, state: MagicMock, refresh_jwt: MagicMock, post: MagicMock):
        """
        Test registration key post method and exception handles

        :param state: mocked state manager
        :type state: MagicMock
        :param refresh_jwt: mocked refresh_jwt method
        :type refresh_jwt: MagicMock
        :param post: mocked post helper method
        :type post: MagicMock
        """
        state.return_value.device = mock_device = Mock(spec=Device)
        # test empty jwt
        mock_device.jwt = None
        mock_device.jwt_payload = None
        # test successful refresh
        refresh_jwt.return_value = True
        with self.assertRaises(ReferenceError):
            self.api_handler.get_registration_key()
        # test failed refresh
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.get_registration_key()
        # test sanity
        mock_device.jwt = backend.SAMPLE_JWT
        mock_device.jwt_payload = backend.SAMPLE_JWT_PAYLOAD
        self.api_handler.get_registration_key()
        post.assert_called_once()
        # test request exceptions
        timeout = self.request_exc.pop('Timeout')
        http = self.request_exc.pop('HTTPError')
        for key, exc in self.request_exc.items():
            with self.subTest("_post_request exception: {}".format(key)):
                post.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.get_registration_key()
        self.request_exc['Timeout'] = timeout
        self.request_exc['HTTPError'] = http
        # test 401 exceptions
        refresh_jwt.return_value = True
        mock_err = Mock().return_value = requests.Response()
        mock_err.status_code = 401
        post.side_effect = requests.exceptions.HTTPError(response=mock_err)
        with self.assertRaises(ReferenceError):
            self.api_handler.get_registration_key()
        refresh_jwt.return_value = False
        with self.assertRaises(ConnectionError):
            self.api_handler.get_registration_key()
        # test response on 404
        mock_err.status_code = 404
        post.side_effect = requests.exceptions.HTTPError(response=mock_err)
        self.assertEqual("ERROR", self.api_handler.get_registration_key())
        # test server error
        mock_err.status_code = 500
        with self.assertRaises(ConnectionError):
            self.api_handler.get_registration_key()
        # Simulate json decode error
        post.side_effect = None
        post.return_value.json = Mock(side_effect=JSONDecodeError("test", "docstring", 10))
        with self.assertRaises(KeyError):
            _ = self.api_handler.get_registration_key()

    @patch.object(ApiHandler, '_get_request', autospec=True)
    def test_request_session_token(self, get: MagicMock):
        """
        Test session token get

        :param get: mocked session.get method
        :type get: MagicMock
        """
        # test sanity
        for val in [True, False]:
            with self.subTest("Response msg: {}".format(val)):
                get.return_value.json.return_value = {'message': val}
                self.api_handler.request_session_token()
        # simulate Timeout retry
        get.reset_mock()
        get.side_effect = self.request_exc['Timeout']
        with self.assertRaises(TimeoutError):
            self.api_handler.request_session_token()
        # remove timeout for this test case
        timeout = self.request_exc.pop('Timeout')
        for key, exc in self.request_exc.items():
            with self.subTest("requests.session.get() exception: {}".format(key)):
                get.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.api_handler.request_session_token()
        self.request_exc['Timeout'] = timeout
        # test json decode error handle
        get.return_value.json = Mock(side_effect=JSONDecodeError("test", "docstring", 10))
        get.side_effect = None
        with self.assertRaises(KeyError):
            self.api_handler.request_session_token()

    @patch.object(ApiHandler, 'request_session_token', autospec=True)
    def test_refresh_jwt(self, mock: MagicMock):
        """
        Test refresh jwt helper method

        :param mock: mocked request_session_token method
        :type mock: MagicMock
        """
        # test success
        self.assertTrue(self.api_handler.refresh_jwt())
        # test connection error handle
        for exc in [TimeoutError, KeyError]:
            with self.subTest("Testing Exception: {}".format(exc)):
                mock.side_effect = exc
                self.assertFalse(self.api_handler.refresh_jwt())
