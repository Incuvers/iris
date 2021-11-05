# -*- coding: utf-8 -*-
"""
Unittests for API Proxy 
=======================
Date: 2021-06

Dependencies:
-------------
```
import unittest
from unittest.mock import Mock
from monitor.events.pipeline import Pipeline
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import copy
import logging
import unittest
from unittest.mock import MagicMock, Mock, call, patch

from tests.resources import models
from monitor.events.event import Event
from monitor.api.proxy import ApiProxy
from monitor.api.cache import ProxyCache
from monitor.imaging.capture import Capture
from monitor.events.pipeline import Pipeline
from monitor.api.api_handler import ApiHandler
from monitor.models.experiment import Experiment
from monitor.environment.state_manager import StateManager


class TestProxy(unittest.TestCase):

    @patch.object(Pipeline, 'stage', lambda self, func, i: None)
    @patch.object(Event, 'register', lambda self, _: None)
    @patch.object(ApiHandler, '__init__', lambda a,b,c: None)
    def setUp(self):
        logging.disable()
        self.proxy = ApiProxy(base_url='localhost',base_path='/v1')

    def tearDown(self):
        del self.proxy
        logging.disable(logging.NOTSET)

    @patch.object(ApiHandler, 'request_session_token')
    @patch.object(ProxyCache, 'execute')
    def test_request_jwt(self, execute: MagicMock, request_session_token: MagicMock):
        """
        Test jwt request helper method and exception handling

        :param execute: mocked execute method
        :type execute: MagicMock
        :param request_session_token: mocked session token endpoint method
        :type request_session_token: MagicMock
        """
        # test sanity
        self.proxy.request_jwt()
        execute.assert_called_once()
        # test exception
        for exc in [TimeoutError, ConnectionError, KeyError]:
            with self.subTest("{} exception test".format(exc)):
                execute.reset_mock()
                request_session_token.side_effect = exc
                self.proxy.request_jwt()
                execute.assert_not_called()

    @patch.object(ApiHandler, 'get_registration_key')
    def test_get_device_registration_key(self, get_registration_key: MagicMock):
        """
        Test device registration key 

        :param get_registration_key: mocked api handler getter
        :type get_registration_key: MagicMock
        """
        self.proxy.get_device_registration_key()
        get_registration_key.assert_called_once()

    @patch.object(Event, 'trigger')
    @patch.object(ApiHandler, 'get_exp_thumbnail')
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    @patch("monitor.api.proxy.cache", lambda: None)
    def test_get_thumbnail(self, state: MagicMock, get_exp_thumbnail: MagicMock, trigger: MagicMock):
        """
        Test thumbnail proxy

        :param state: [description]
        :type state: MagicMock
        :param get_exp_thumbnail: [description]
        :type get_exp_thumbnail: MagicMock
        :param trigger: [description]
        :type trigger: MagicMock
        """
        state.return_value.experiment = exp = Mock(spec=Experiment)
        # test sanity
        exp.active = True
        self.proxy.get_thumbnail()
        get_exp_thumbnail.assert_called_once()
        trigger.assert_called_once()
        # test inactive experiment
        get_exp_thumbnail.reset_mock()
        exp.active = False
        self.proxy.get_thumbnail()
        get_exp_thumbnail.assert_not_called()

    @patch.object(Pipeline, 'begin')
    @patch.object(ApiHandler, 'get_device_info', lambda _: models.DEVICE_MODEL)
    @patch.object(ApiHandler, 'get_device_avatar')
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_device_info_and_avatar(self, state: MagicMock, get_device_avatar: MagicMock, begin: MagicMock):
        """
        Test device info and avatar proxy

        :param state: [description]
        :type state: MagicMock
        :param get_device_avatar: [description]
        :type get_device_avatar: MagicMock
        :param begin: [description]
        :type begin: MagicMock
        """
        # test sanity
        self.proxy.get_device_info_and_avatar()
        begin.assert_called_once()
        state.return_value.commit.assert_called_once()
        # test key error in avatar get
        begin.reset_mock()
        state.return_value.commit.reset_mock()
        get_device_avatar.side_effect = KeyError
        self.proxy.get_device_info_and_avatar()
        begin.assert_not_called()
        state.return_value.commit.assert_called_once()

    @patch.object(ApiHandler, 'get_protocol', lambda self, _: models.PROTOCOL_MODEL)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_protocol(self, state: MagicMock):
        """
        Test protocol proxy

        :param state: [description]
        :type state: MagicMock
        """
        self.proxy.get_protocol(1)
        state.return_value.commit.assert_called_once()

    @patch.object(ApiHandler, 'get_experiment')
    @patch.object(ApiProxy, 'get_protocol', lambda self, _: None)
    @patch.object(ApiProxy, 'get_imaging_profile', lambda self, _: None)
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_experiment(self, state: MagicMock, get_experiment: MagicMock):
        """
        Test experiment proxy

        :param state: [description]
        :type state: MagicMock
        :param get_experiment: [description]
        :type get_experiment: MagicMock
        """
        # test experiment fetch
        self.proxy.get_experiment()
        state.return_value.commit.assert_called_once()
        # test experiment cancel
        state.return_value.commit.reset_mock()
        get_experiment.return_value = "None"
        self.proxy.get_experiment()
        state.return_value.commit.assert_called_once()

    @patch.object(ApiHandler, 'get_imaging_profile', lambda self, _: copy.deepcopy(models.IMAGING_PROFILE_MODEL))
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_get_imaging_profile(self, state: MagicMock):
        """
        Test imaging profile proxy

        :param state: [description]
        :type state: MagicMock
        """
        # test successful state commit
        state.return_value.commit.return_value = True
        self.proxy.get_imaging_profile(1)
        state.return_value.commit.assert_called_once()
        # test unsuccessful state commit
        state.return_value.commit.reset_mock()
        state.return_value.commit.return_value = False
        self.proxy.get_imaging_profile(1)
        state.return_value.commit.assert_called_once()

    @patch.object(ApiHandler, 'post_img')
    @patch.object(StateManager, '__enter__')
    def test_upload_images(self, state: MagicMock, post_img: MagicMock):
        """
        Test recursive experiment image posting method

        :param post_img: [description]
        :type post_img: MagicMock
        """
        img_id = 1
        exp_id = 1
        post_img.return_value = img_id
        first = {
            'type': 'DPC_0',
            'image_id': None
        }
        second = {
            'type': 'DPC_1',
            'image_id': img_id
        }
        third = {
            'type': 'DPC_2',
            'image_id': img_id
        }
        fourth = {
            'type': 'DPC_3',
            'image_id': img_id
        }
        fifth = {
            'type': 'GFP',
            'image_id': img_id
        }
        state.return_value.experiment.id = exp_id
        captures = Mock(spec=Capture)
        captures.captures = [1, 2, 3, 4, 5]
        captures.get_processed.return_value = file_payload = Mock()
        self.proxy.upload_images(captures)
        post_img.assert_has_calls(
            [
                call(first, exp_id, file_payload),
                call(second, exp_id, file_payload),
                call(third, exp_id, file_payload),
                call(fourth, exp_id, file_payload),
                call(fifth, exp_id, file_payload)
            ]
        )

    @patch.object(ApiHandler, 'post_preview')
    def test_upload_preview(self, post_preview: MagicMock):
        """
        Test recursive preview posting method

        :param post_preview: [description]
        :type post_preview: MagicMock
        """
        gfp = True
        first = {
            'type': 'DPC_0',
            'is_gfp': gfp
        }
        second = {
            'type': 'DPC_1',
            'is_gfp': gfp
        }
        third = {
            'type': 'DPC_2',
            'is_gfp': gfp
        }
        fourth = {
            'type': 'DPC_3',
            'is_gfp': gfp
        }
        fifth = {
            'type': 'GFP',
            'is_gfp': gfp
        }
        captures = Mock(spec=Capture)
        captures.captures = [1, 2, 3, 4, 5]
        captures.gfp_capture = gfp
        captures.get_processed.return_value = file_payload = Mock()
        self.proxy.upload_preview(captures)
        post_preview.assert_has_calls(
            [
                call(first, file_payload),
                call(second, file_payload),
                call(third, file_payload),
                call(fourth, file_payload),
                call(fifth, file_payload)
            ]
        )

    @patch.object(ApiHandler, 'post_calibration_time')
    def test_send_co2_calibration_time(self, post_calibration_time: MagicMock):
        """
        Test co2 calibration proxy

        :param post_calibration_time: [description]
        :type post_calibration_time: MagicMock
        """
        time = "test"
        payload = {
            'iso_date': time
        }
        self.proxy.send_co2_calibration_time(time)
        post_calibration_time.assert_called_once_with(payload)

    def test_migrate(self):
        """
        Test payload migrations
        """
        # test ref underload
        ref = {'field1': 1, 'field2': 2}
        digest = {'field1': 2}
        migrated = self.proxy.migrate(ref, digest, Mock())
        self.assertDictEqual(migrated, {'field1': 2, 'field2': 2})
        # test ref overload
        ref = {'field4': False, 'field3': "default"}
        digest = {'field1': True, 'field2': 2, 'field3': "test"}
        migrated = self.proxy.migrate(ref, digest, Mock())
        self.assertDictEqual(migrated, {'field4': False, 'field3': "test"})
