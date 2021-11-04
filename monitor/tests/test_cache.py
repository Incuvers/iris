# -*- coding: utf-8 -*-
"""
Unittests for System Cache
==========================
Date: 2021-05

Dependencies:
-------------
```
import os
import unittest
from pathlib import Path
from json.decoder import JSONDecodeError
from unittest.mock import MagicMock, Mock, call, patch, mock_open

from monitor.events.event import Event
from monitor.models.device import Device
from monitor.cache.cache import SystemCache
from monitor.models.protocol import Protocol
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

from datetime import datetime
import logging
import os
import copy
import unittest
from pathlib import Path
from json.decoder import JSONDecodeError
from unittest.mock import MagicMock, Mock, patch, mock_open
from freezegun import freeze_time

from monitor.events.pipeline import Pipeline
from monitor.tests.resources import models
from monitor.events.event import Event
from monitor.models.device import Device
from monitor.environment.cache import SystemCache
from monitor.models.protocol import Protocol
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile


class TestCache(unittest.TestCase):

    @patch.object(os, 'makedirs')
    @patch.object(Pipeline, 'stage', lambda x, y, z: None)
    @patch.object(Event, 'register', lambda x, y: None)
    def setUp(self, _: MagicMock):
        logging.disable()
        self.cache = SystemCache()

    def tearDown(self):
        del self.cache
        logging.disable(logging.NOTSET)

    @patch.object(SystemCache, 'read')
    @patch.object(copy, 'deepcopy')
    def test_get_protocol(self, deepcopy: MagicMock, read: MagicMock):
        """
        Test protocol runtime model load

        :param deepcopy: [description]
        :type deepcopy: MagicMock
        :param read: [description]
        :type read: MagicMock
        """
        # test sanity
        mock_protocol = Mock(spec=Protocol)
        mock_protocol.configure_mock(**models.PROTOCOL_MODEL)
        deepcopy.return_value = mock_protocol
        read.return_value = models.PROTOCOL_SERIALIZED

        protocol = self.cache.get_protocol()
        read.assert_called_once_with('protocol.json')
        self.assertEqual(protocol, mock_protocol)
        # test read exception
        for exc in [FileNotFoundError, JSONDecodeError("", "", 1)]:
            with self.subTest("Testing read exception: {}".format(exc)):
                read.side_effect = exc
                self.assertEqual(self.cache.get_protocol(), mock_protocol)

    @patch.object(SystemCache, 'read')
    @patch.object(copy, 'deepcopy')
    def test_get_imaging_profile(self, deepcopy: MagicMock, read: MagicMock):
        """
        Test imaging profile runtime model load

        :param deepcopy: [description]
        :type deepcopy: MagicMock
        :param read: [description]
        :type read: MagicMock
        """
        # test sanity
        mock_ip = Mock(spec=ImagingProfile)
        mock_ip.configure_mock(**models.IMAGING_PROFILE_MODEL)
        deepcopy.return_value = mock_ip
        read.return_value = models.IMAGING_PROFILE_MODEL
        imaging_profile = self.cache.get_imaging_profile()
        read.assert_called_once_with('imaging.json')
        self.assertEqual(imaging_profile, mock_ip)
        # test read exception
        for exc in [FileNotFoundError, JSONDecodeError("", "", 1)]:
            with self.subTest("Testing read exception: {}".format(exc)):
                read.side_effect = exc
                self.assertEqual(self.cache.get_imaging_profile(), mock_ip)

    @patch.object(SystemCache, 'read')
    @patch.object(SystemCache, 'clear_thumbnail')
    @patch.object(copy, 'deepcopy')
    def test_get_experiment(self, deepcopy: MagicMock, clear_thumbnail: MagicMock, read: MagicMock):
        """
        Test get experiment runtime model.
        """
        # test sanity
        mock_exp = Mock(spec=Experiment)
        mock_exp.configure_mock(**models.EXPERIMENT_MODEL)
        mock_exp.end_at = datetime.fromisoformat(models.ISO_DATETIME_END)
        deepcopy.return_value = mock_exp
        read.return_value = models.EXPERIMENT_SERIALIZED
        dt = datetime.fromtimestamp(datetime.fromisoformat(
            models.ISO_DATETIME_START).timestamp() - 1000)
        with freeze_time(dt):
            self.assertEqual(self.cache.get_experiment(), mock_exp)
        clear_thumbnail.assert_not_called()
        read.assert_called_once_with('experiment.json')
        read.reset_mock()
        # test expired experiment
        with freeze_time(datetime.fromisoformat(models.ISO_DATETIME_END)):
            self.assertEqual(self.cache.get_experiment(), mock_exp)
        read.assert_called_once_with('experiment.json')
        clear_thumbnail.assert_called()
        # test read exception
        for exc in [FileNotFoundError, JSONDecodeError("", "", 1)]:
            with self.subTest("Testing read exception: {}".format(exc)):
                read.side_effect = exc
                self.assertEqual(self.cache.get_experiment(), mock_exp)

    @patch.object(SystemCache, 'read')
    @patch.object(SystemCache, 'write')
    @patch.object(SystemCache, 'read_lab_id')
    @patch.object(copy, 'deepcopy')
    def test_get_device(self, deepcopy: MagicMock, read_lab_id: MagicMock, write: MagicMock, read: MagicMock):
        """
        Test get device runtime model.
        """
        read_lab_id.return_value = 1
        # test sanity
        mock_device = Mock(spec=Device)
        mock_device.configure_mock(**models.DEVICE_MODEL)
        deepcopy.return_value = mock_device
        read.return_value = models.DEVICE_MODEL
        self.assertEqual(self.cache.get_device(), mock_device)
        read.assert_called_once_with('device.json')
        # test read exception
        for exc in [FileNotFoundError, JSONDecodeError("", "", 1)]:
            with self.subTest("Testing read exception: {}".format(exc)):
                read.side_effect = exc
                self.assertEqual(self.cache.get_device(), mock_device)
                write.assert_called_once()
                write.reset_mock()

    @patch.object(Path, 'exists', **{'return_value': True})
    @patch.object(Event, 'trigger', autospec=True)
    def test_load_thumbnail(self, mock_event: MagicMock, _: MagicMock):
        """
        Test load experiment thumbnail and event trigger

        :param mock_event: mocked event object
        :type mock_event: MagicMock
        :param _: mocked path.exist function call with return True
        :type _: MagicMock
        """
        self.cache.load_thumbnail()
        mock_event.assert_called_once()

    @patch('builtins.open', _open=mock_open(), create=True)
    @patch('json.dump')
    def test_write(self, mock_js_dump: MagicMock, _open: MagicMock):
        """
        Test cache writes
        """
        # test all models write
        for model in [Mock(spec=ImagingProfile), Mock(spec=Device), Mock(spec=Experiment), Mock(spec=Protocol)]:
            with self.subTest("Testing model {} cache write".format(model)):
                self.cache.write(model)
                _open.assert_called_once()
                _open.reset_mock()
                mock_js_dump.assert_called_once()
                mock_js_dump.reset_mock()

    @patch.object(os, 'remove')
    @patch('builtins.open', _open=mock_open(), create=True)
    def test_write_lab_id(self, mock_cm: MagicMock, _open: MagicMock, _remove: MagicMock):
        """
        Test lab id write method

        :param mock_cm: [description]
        :type mock_cm: MagicMock
        """
        mock_cm.return_value.get_env.return_value = os.environ.get("COMMON")
        # test ip model write
        self.cache.write_lab_id(None)
        _remove.assert_called_once()
        _open.return_value.__enter__.assert_not_called()
        _open.reset_mock()
        self.cache.write_lab_id(1)
        _open.return_value.__enter__.return_value.write.assert_called_with("1")

    @patch('builtins.open', _open=mock_open(), create=True)
    def test_write_device_avatar(self, _open: MagicMock):
        """
        Test device avatar write
        """
        # test ip model write
        self.cache.write_device_avatar(b'')
        _open.return_value.__enter__.return_value.write.assert_called_with(b'')

    @patch('builtins.open', _open=mock_open(), create=True)
    def test_write_thumbnail(self, _open: MagicMock):
        """
        Test device avatar write
        """
        # test ip model write
        self.cache.write_thumbnail(b'')
        _open.return_value.__enter__.return_value.write.assert_called_with(b'')

    @patch('builtins.open', _open=mock_open(read_data="data"))
    @patch('json.load')
    def test_read_lab_id(self, load: MagicMock, _open: MagicMock):
        """
        Test lab id file parsing.
        """
        _open.side_effect = FileNotFoundError
        self.assertEqual(self.cache.read_lab_id(), None)
        _open.side_effect = None
        self.assertEqual(self.cache.read_lab_id(), 1)

    @patch('builtins.open', mock_open(read_data="data"))
    @patch('json.load')
    def test_read(self, mock_cm: MagicMock, mock_js_load: MagicMock):
        """
        Test cache volume reads

        :param mock_js_load: mocked json.load function
        :type mock_js_load: MagicMock
        """
        mock_cm.return_value.get_env.return_value = os.environ.get("MONITOR_CACHE")
        mock_payload = Mock(spec=dict)
        mock_js_load.return_value = mock_payload
        self.assertTrue(self.cache.read("test.json") is mock_payload)

    @patch.object(os, 'remove')
    def test_clear(self, mock_cm: MagicMock, mock_os: MagicMock):
        """
        Test removal of cache runtime object artefacts

        :param mock_os: mocked os module
        :type mock_os: MagicMock
        """
        # test sanity
        mock_cm.return_value.get_env.return_value = os.environ.get("MONITOR_CACHE")
        self.cache.clear("test.json")
        mock_os.assert_called_once_with("{}/test.json".format(os.environ.get("MONITOR_CACHE")))
        # test file not found exception handle
        mock_os.reset_mock()
        mock_os.side_effect = FileNotFoundError
        self.cache.clear("nonexistant.json")

    @patch.object(os, 'remove')
    def test_clear_thumbnail(self, mock_cm: MagicMock, mock_os: MagicMock):
        """
        Test removal of experiment thumbnail image from cache volume

        :param mock_os: mocked os module
        :type mock_os: MagicMock
        """
        # test sanity
        mock_cm.return_value.get_env.return_value = os.environ.get("COMMON")
        self.cache.clear_thumbnail()
        mock_os.assert_called_once_with("{}/thumbnail.png".format(os.environ.get("COMMON")))
        # test file not found handle
        mock_os.reset_mock()
        mock_os.side_effect = FileNotFoundError
        self.cache.clear_thumbnail()
