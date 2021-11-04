#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unittest for Mqtt
=================
Modified: 2021-03

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import asyncio
import json
import os
import time
import unittest
import imp
from json.decoder import JSONDecodeError
from freezegun import freeze_time
from copy import deepcopy
from datetime import datetime
from typing import Optional
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from AWSIoTPythonSDK.exception import AWSIoTExceptions
from unittest.mock import MagicMock, Mock, call, patch
from monitor.models.device import Device
from monitor.ui.static.settings import UISettings as uis
from monitor.exceptions.mqtt import ImageTopicError
from monitor.models.imaging_profile import ImagingProfile
from monitor.events.event import Event
from monitor.events.pipeline import Pipeline
from monitor.cloud import mqtt
from monitor.models.icb import ICB
from monitor.imaging import constants as IC
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import StateManager

from monitor.tests import resources


class TestMQTT(unittest.TestCase):

    @patch.object(AWSIoTMQTTShadowClient, 'configureEndpoint', lambda self, a, b: None)
    @patch.object(AWSIoTMQTTShadowClient, 'configureCredentials', lambda self, a, KeyPath, CertificatePath: None)
    @patch.object(AWSIoTMQTTShadowClient, 'getMQTTConnection', **{'return_value': Mock(spec=AWSIoTMQTTShadowClient)})
    def setUp(self, _: MagicMock):
        def kill_patches():  # Create a cleanup callback that undoes our patches
            patch.stopall()  # Stops all patches started with start()
            imp.reload(mqtt)  # Reload our mqtt module which restores the original decorator
        # We want to make sure this is run so we do this in addCleanup instead of tearDown
        self.addCleanup(kill_patches)
        # Now patch the decorator where the decorator is being imported from
        # The lambda makes our decorator into a pass-thru. Also, don't forget to call start()
        patch('monitor.environment.thread_manager.ThreadManager.threaded',
              lambda *x, **y: lambda f: f).start()
        patch('monitor.environment.thread_manager.ThreadManager.set_name',
              lambda *x, **y: lambda f: f).start()
        patch('monitor.environment.thread_manager.ThreadManager.lock',
              lambda *x, **y: lambda f: f).start()
        imp.reload(mqtt)  # Reloads the mqtt.py module which applies our patched decorator
        self.mqtt = mqtt.MQTT()

    def tearDown(self):
        del self.mqtt

    @patch.object(StateManager, '__enter__')
    @patch.object(time, 'sleep', side_effect=InterruptedError)
    @patch.object(events, 'system_status')
    def test_start(self, mock_ss: MagicMock, _: MagicMock, mock_sm: MagicMock):
        mock_sm.return_value.device = Mock(spec=Device)
        self.mqtt._configure_connection = Mock()
        self.mqtt.shadow_document_init = Mock()
        self.mqtt._report_telemetry = Mock()
        self.mqtt._on_connect = Mock()
        # first vanilla pass
        self.mqtt.start()
        self.mqtt._configure_connection.assert_called_once()
        self.mqtt.shadow_document_init.assert_called_once()
        self.mqtt._report_telemetry.assert_called_once()
        self.mqtt._on_connect.assert_called_once()
        mock_ss.trigger.assert_called_once()
        # second pass, raise ConnectionError
        self.mqtt._configure_connection.reset_mock()
        self.mqtt.shadow_document_init.reset_mock()
        self.mqtt._report_telemetry.reset_mock()
        self.mqtt._on_connect.reset_mock()
        mock_sm.reset_mock()
        mock_ss.reset_mock()
        self.mqtt.shadow_document_init.side_effect = ConnectionError
        with self.assertRaises(InterruptedError):
            self.mqtt.start()
        self.mqtt._configure_connection.assert_called_once()
        self.mqtt.shadow_document_init.assert_called_once()
        self.mqtt._report_telemetry.assert_not_called()
        self.mqtt._on_connect.assert_not_called()
        mock_ss.trigger.assert_called_once()

    @patch.object(StateManager, '__enter__')
    @patch.object(Event, 'trigger')
    @patch('monitor.cloud.mqtt.MQTT._report_shadow')
    def test_on_connect(self, _report_shadow: MagicMock, trigger: MagicMock, mock_sm: MagicMock):
        """
        :param mock_cs: mock connection_status
        :type mock_cs: MagicMock
        :param mock_ss: mock system_status]
        :type mock_ss: MagicMock
        :param mock_tm: mock StateManager
        :type mock_tm: MagicMock
        """
        self.mqtt.shadow = Mock()
        mock_sm.return_value.device = device = Mock()
        self.mqtt._on_connect()
        _report_shadow.assert_called_once_with(
            payload={'state': {'reported': {"is_online": True}}})
        trigger.assert_called_once()
        mock_sm.return_value.commit.assert_called_once_with(device)

    @patch.object(StateManager, '__enter__')
    @patch.object(Event, 'trigger')
    def test_on_disconnect(self, trigger: MagicMock, mock_sm: MagicMock):
        """
        :param mock_cs: mock connection_status
        :type mock_cs: MagicMock
        :param mock_ss: mock system_status
        :type mock_ss: MagicMock
        """
        self.mqtt.shadow = Mock()
        mock_sm.return_value.device = device = Mock()
        self.mqtt._on_disconnect()
        trigger.assert_called_once_with(status=uis.STATUS_OK)
        mock_sm.return_value.commit.assert_called_once_with(device)

    def test__configure_connection(self):
        # mock all used inherited methods
        self.mqtt.configureAutoReconnectBackoffTime = Mock()
        self.mqtt.configureConnectDisconnectTimeout = Mock()
        self.mqtt.configureMQTTOperationTimeout = Mock()
        self.mqtt.client = Mock()
        self.mqtt.client.subscribe = Mock()

        self.mqtt.configureLastWill = Mock()
        self.mqtt.connect = Mock()
        self.mqtt.createShadowHandlerWithName = Mock()
        self.mqtt.shadow = Mock()
        # vanilla pass
        self.mqtt._configure_connection()
        # test connect exceptions
        for exc in [AWSIoTExceptions.connectTimeoutException, AWSIoTExceptions.connectError(12)]:
            with self.subTest("connect() exception: {}".format(exc)):
                self.mqtt.connect.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.mqtt._configure_connection()
        self.mqtt.connect.side_effect = None
        # test subscribe exceptions
        for exc in [AWSIoTExceptions.subscribeTimeoutException, AWSIoTExceptions.subscribeError(12)]:
            with self.subTest("subscribe() exception: {}".format(exc)):
                # timeout exp from subscribe
                self.mqtt.client.subscribe.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.mqtt._configure_connection()

    def test_shadow_document_init(self):
        mock_shadow_get = Mock()
        self.mqtt.shadow = Mock()
        self.mqtt.shadow.shadowGet = mock_shadow_get

        # vanilla
        self.mqtt.shadow_document_init()
        mock_shadow_get.assert_called_once()
        mock_shadow_get.reset_mock()

        # test subscribe exceptions
        for exc in [AWSIoTExceptions.subscribeTimeoutException, AWSIoTExceptions.subscribeError(12)]:
            with self.subTest("subscribe() exception: {}".format(exc)):
                # timeout exp from subscribe
                mock_shadow_get.side_effect = exc
                with self.assertRaises(ConnectionError):
                    self.mqtt.shadow_document_init()
                mock_shadow_get.assert_called_once()
            mock_shadow_get.reset_mock()
            mock_shadow_get.side_effect = None

    @patch.object(json, 'loads')
    @patch('monitor.cloud.mqtt.MQTT._report_shadow')
    @patch('monitor.cloud.mqtt.MQTT._generate_shadow_document', lambda _: resources.SHADOW_DOCUMENT)
    def test_shadow_get_response(self, _report_shadow: MagicMock, loads: MagicMock):
        """
        Test shadow get response and shadow validation checks

        :param _report_shadow: [description]
        :type _report_shadow: MagicMock
        :param loads: [description]
        :type loads: MagicMock
        """
        # test rejected response
        self.mqtt._shadow_get_response("", "timeout")
        loads.assert_not_called()
        # test accepted bad shadow
        loads.return_value = {'state': {'desired': {}}}
        self.mqtt._shadow_get_response("", "accepted")
        _report_shadow.assert_called_once_with(payload={'state': resources.SHADOW_DOCUMENT})

    @patch('monitor.cloud.mqtt.MQTT._report_shadow')
    def test_update_sensorframe(self, _report_shadow: MagicMock):
        """
        Test async sensorframe (ICB) subscriber function

        :param _report_shadow: [description]
        :type _report_shadow: MagicMock
        """
        sensorframe = ICB()
        sensorframe.tp = 25.0
        sensorframe.op = 1.0
        sensorframe.cp = 5.4
        setpoint_payload = {
            'TP': sensorframe.tp,
            'OP': sensorframe.op,
            'CP': sensorframe.cp
        }
        state_payload = {
            'state':
            {
                'desired': setpoint_payload,
                'reported': setpoint_payload,
            }
        }
        asyncio.run(self.mqtt.update_sensorframe(sensorframe))
        _report_shadow.assert_called_once_with(payload=state_payload)

    @patch('monitor.cloud.mqtt.MQTT._report_shadow')
    def test_update_imaging_settings(self, _report_shadow: MagicMock):
        """
        Test async imaging profile subscriber function

        :param _report_shadow: [description]
        :type _report_shadow: MagicMock
        """
        imaging_settings_payload = {
            'state':
            {
                'desired':
                {
                    'imaging_settings': resources.DEFAULT_IMAGING_PROFILE_PAYLOAD
                },
                'reported':
                {
                    'imaging_settings': resources.DEFAULT_IMAGING_PROFILE_PAYLOAD,
                }
            }
        }
        ip = Mock(spec=ImagingProfile)
        ip.dpc_exposure = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('dpc_exposure')
        ip.dpc_exposure_min = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('dpc_exposure_min')
        ip.dpc_exposure_max = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('dpc_exposure_max')
        ip.gfp_exposure = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('gfp_exposure')
        ip.gfp_exposure_min = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('gfp_exposure_min')
        ip.gfp_exposure_max = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('gfp_exposure_max')
        ip.dpc_gain = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('dpc_gain')
        ip.gfp_gain = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('gfp_gain')
        ip.gain_min = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('gain_min')
        ip.gain_max = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('gain_max')
        ip.dpc_brightness = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('dpc_brightness')
        ip.gfp_brightness = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('gfp_brightness')
        ip.brightness_min = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('brightness_min')
        ip.brightness_max = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('brightness_max')
        ip.dpc_inner_radius = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('dpc_inner_radius')
        ip.dpc_outer_radius = resources.DEFAULT_IMAGING_PROFILE_PAYLOAD.get('dpc_outer_radius')
        asyncio.run(self.mqtt.update_imaging_settings(ip))
        _report_shadow.assert_called_once_with(payload=imaging_settings_payload)

    @patch.object(json, 'loads')
    @patch.object(Pipeline, 'begin')
    def test_img_topic_resolver(self, begin: MagicMock, loads: MagicMock):
        """
        Test all mqtt image notification types

        :param begin: [description]
        :type begin: MagicMock
        """
        # test bad payload
        for exc in [TypeError, JSONDecodeError("", "", 1)]:
            with self.subTest("Testing loads exception: {}".format(exc)):
                loads.side_effect = exc
                with self.assertRaises(ImageTopicError):
                    self.mqtt._img_topic_resolver("", "", Mock())
        # test experiment conditional
        loads.side_effect = None
        loads.return_value = {'type': 'experiment'}
        self.mqtt._img_topic_resolver("", "", Mock())
        begin.assert_called_once_with()
        begin.reset_mock()
        # test dpc preview conditional
        loads.return_value = {'type': 'dpc-capture'}
        self.mqtt._img_topic_resolver("", "", Mock())
        begin.assert_called_with(gfp=False)
        begin.reset_mock()
        # test gfp preview conditional
        loads.return_value = {'type': 'gfp-capture'}
        self.mqtt._img_topic_resolver("", "", Mock())
        begin.assert_called_with(gfp=True)

    @patch.object(json, 'loads')
    @patch.object(Event, 'trigger', lambda self, _: None)
    @patch('monitor.cloud.mqtt.MQTT.filter_delta')
    @patch('monitor.cloud.mqtt.MQTT._delta_resolver')
    def test_shadow_delta_response(self, delta_resolver: MagicMock, filter_delta: MagicMock, loads: MagicMock):
        """
        Test shadow delta response method

        :param delta_resolver: [description]
        :type delta_resolver: MagicMock
        :param filter_delta: [description]
        :type filter_delta: MagicMock
        :param loads: [description]
        :type loads: MagicMock
        """
        # test not accepted
        self.mqtt._shadow_delta_response("", "timeout", "")
        loads.assert_not_called()
        # test accepted and request key
        filter_delta.return_value = {'jwt': resources.SAMPLE_JWT}
        self.mqtt._shadow_delta_response("", f"delta/{self.override('UUID')}", "")
        delta_resolver.assert_called_once_with({'jwt': resources.SAMPLE_JWT})
        delta_resolver.reset_mock()
        # test accepted and no request key
        filter_delta.return_value = {}
        self.mqtt._shadow_delta_response("", f"delta/{self.override('UUID')}", "")
        delta_resolver.assert_not_called()

    @patch('monitor.cloud.mqtt.MQTT._report_shadow')
    @patch.object(StateManager, '__enter__')
    @patch('monitor.cloud.mqtt.MQTT.resolve_device_refresh')
    @patch('monitor.cloud.mqtt.MQTT.resolve_experiment_refresh')
    @patch('monitor.cloud.mqtt.MQTT.resolve_protocol_refresh')
    def test_delta_resolver(self, rpr: MagicMock, rer: MagicMock, rdr: MagicMock, state: MagicMock,
                            _report_shadow: MagicMock):
        """
        Test delta resolver state commits, thread execs and validator failures

        :param state: [description]
        :type state: MagicMock
        :param tm: [description]
        :type tm: MagicMock
        :param _report_shadow: [description]
        :type _report_shadow: MagicMock
        """
        state.return_value = Mock(spec=StateManager)
        state.return_value.device = device = Mock(spec=Device)
        state.return_value.icb = icb = Mock(spec=ICB)
        state.return_value.imaging_profile = imaging_profile = Mock(
            spec=ImagingProfile)
        # test all conditionals pass
        state.return_value.commit = Mock(return_value=True)
        requests = {
            "jwt": resources.SAMPLE_JWT,
            "refresh": {
                "device": "2021-05-07T19:44:04.876065+00:00",
                "experiment": "2021-04-30T21:54:48.002+00:00",
                "customer": "2021-04-30T21:54:48.002+00:00",
                "protocol": "2021-04-30T21:54:48.002+00:00"
            },
            "TP": 34,
            "CP": 6,
            "OP": 4,
            "imaging_settings": {
                "dpc_brightness": 168,
                "dpc_gain": 4,
                "dpc_exposure": 11840,
                "gfp_brightness": 168,
                "gfp_gain": 60,
                "gfp_exposure": 756438,
                "dpc_inner_radius": 3,
                "dpc_outer_radius": 4,
                "imaging_profile_id": -1,
                "name": "Default Profile",
                "gain_min": 4,
                "gain_max": 63,
                "brightness_min": 0,
                "brightness_max": 4096,
                "gfp_capture": True,
                "gfp_exposure_min": 100000,
                "gfp_exposure_max": 2000000,
                "dpc_exposure_min": 2000,
                "dpc_exposure_max": 15000
            }
        }
        self.mqtt._delta_resolver(requests)
        for resolver in [rer, rdr, rpr]:
            resolver.assert_called_once()
            resolver.reset_mock()
        state.return_value.commit.assert_has_calls(
            [
                call(device),
                call(icb),
                call(icb),
                call(icb),
                call(imaging_profile)
            ]
        )
        _report_shadow.assert_called_once_with(payload={'state': {'reported': requests}})
        _report_shadow.reset_mock()
        # test validator failure
        ref = deepcopy(requests)
        state.return_value.commit.return_value = False
        self.mqtt._delta_resolver(requests)
        state.return_value.commit.assert_has_calls(
            [
                call(device),
                call(icb),
                call(icb),
                call(icb),
                call(imaging_profile)
            ]
        )
        ref.pop("imaging_settings")
        ref.pop("TP")
        ref.pop("OP")
        ref.pop("CP")
        ref.pop("jwt")
        _report_shadow.assert_called_once_with(payload={'state': {'reported': ref}})

    @freeze_time(resources.ISO_DATETIME)
    def test_package_telemetry(self):
        """
        Test telemetry packaging helper
        """
        # test uninitialized state
        self.assertEqual(self.mqtt._package_telemetry(), {})
        # test long publish
        self.mqtt.last_lpt_publish = round(datetime.fromisoformat(
            resources.ISO_DATETIME).timestamp() - 15 * 60)
        with patch.object(StateManager, '__enter__') as state:
            state.return_value.icb = Mock(spec=ICB)
            payload = self.mqtt._package_telemetry()
        self.assertEqual(payload.get('ttl'), 0)
        self.assertEqual(payload.get('point_type'), 1)
        # test short publish
        self.mqtt.last_lpt_publish = round(datetime.fromisoformat(
            resources.ISO_DATETIME).timestamp() + 15 * 60)
        with patch.object(StateManager, '__enter__') as state:
            state.return_value.icb = Mock(spec=ICB)
            payload = self.mqtt._package_telemetry()
        self.assertEqual(payload.get('ttl'), datetime.fromisoformat(
            resources.ISO_DATETIME).timestamp() + 120)
        self.assertEqual(payload.get('point_type'), 0)

    @patch.object(time, 'sleep', side_effect=InterruptedError)
    @patch.object(StateManager, '__enter__')
    def test_report_telemetry(self, mock_sm: MagicMock, _: MagicMock):
        """
        Test telemetry event loop and exception handling

        :param mock_sm: [description]
        :type mock_sm: MagicMock
        :param _: [description]
        :type _: MagicMock
        """
        # verify with no experiment
        mock_client = Mock()
        mock_publish = Mock()
        self.mqtt.client = mock_client
        self.mqtt.client.publish = mock_publish
        self.mqtt._package_telemetry = Mock()
        self.mqtt._package_telemetry.return_value = resources.DEFAULT_TELEMETRY_PAYLOAD
        mock_exp = Mock()
        mock_sm.return_value.experiment = mock_exp
        mock_exp.active = False
        with self.assertRaises(InterruptedError):
            self.mqtt._report_telemetry()
        self.mqtt._package_telemetry.assert_called_once()
        mock_publish.assert_called_once()
        topic, telemetry_str, qos = mock_publish.call_args[0]
        self.assertEqual(qos, 0)
        telemetry_dict = json.loads(telemetry_str)  # convert to dict
        self.assertTrue(telemetry_dict['exp_id'] == "-1")
        mock_exp.reset_mock()
        mock_publish.reset_mock()
        self.mqtt._package_telemetry.reset_mock()
        mock_exp.active = True
        mock_exp.id = "123"
        with self.assertRaises(InterruptedError):
            self.mqtt._report_telemetry()
        mock_publish.assert_called()
        topic, telemetry_str, qos = mock_publish.call_args[0]
        telemetry_dict = json.loads(telemetry_str)  # convert to dict
        self.assertTrue(telemetry_dict['exp_id'] == "123")
        mock_exp.reset_mock()
        mock_publish.side_effect = AWSIoTExceptions.publishTimeoutException
        with self.assertRaises(InterruptedError):
            self.mqtt._report_telemetry()

    @freeze_time(datetime.fromisoformat(resources.ISO_DATETIME))
    @patch.object(StateManager, '__enter__', **{'return_value': Mock(spec=StateManager)})
    def test_generate_shadow_document(self, state: MagicMock):
        """
        Test shadow document generation method

        :param state: [description]
        :type state: MagicMock
        """
        state.return_value.device = device = Mock(spec=Device)
        device.jwt = resources.SAMPLE_JWT
        shadow_template = {
            "desired":
            {
                "TP": ICB.TP_DEFAULT,
                "CP": ICB.CP_DEFAULT,
                "OP": ICB.OP_DEFAULT,
                "refresh":
                {
                    "device": resources.ISO_DATETIME,
                    "experiment": resources.ISO_DATETIME,
                    "customer": resources.ISO_DATETIME,
                    "protocol": resources.ISO_DATETIME
                },
                "jwt": resources.SAMPLE_JWT,
                "imaging_settings": IC.DEFAULT_IP_PAYLOAD
            },
            "reported":
            {
                "is_online": True,
                "TP": ICB.TP_DEFAULT,
                "CP": ICB.CP_DEFAULT,
                "OP": ICB.OP_DEFAULT,
                "refresh":
                {
                    "device": resources.ISO_DATETIME,
                    "experiment": resources.ISO_DATETIME,
                    "customer": resources.ISO_DATETIME,
                    "protocol": resources.ISO_DATETIME
                },
                "jwt": resources.SAMPLE_JWT,
                "imaging_settings": IC.DEFAULT_IP_PAYLOAD
            }
        }
        self.assertDictEqual(self.mqtt._generate_shadow_document(), shadow_template)

    @patch.object(json, 'dumps')
    def test__report_shadow(self, dumps: MagicMock):
        """
        Test shadow report

        :param dumps: [description]
        :type dumps: MagicMock
        """
        # test no shadow
        self.mqtt._report_shadow({'mock': 'payload'})
        dumps.assert_not_called()
        # test sanity
        self.mqtt.shadow = Mock()
        self.mqtt._report_shadow({'mock': 'payload'})

    def test_shadow_update_response(self):
        """
        Test logging statements for shadow update callback
        """
        # test accepted
        self.mqtt._shadow_update_response("{'mock': 'payload'}", "accepted", "")
        # else condition
        self.mqtt._shadow_update_response("{'mock': 'payload'}", "timeout", "")

    def test_filter_delta(self):
        """
        Test dictionary delta comparator method
        """
        # test full incoming delta load
        self.assertDictEqual(self.mqtt.filter_delta(
            {}, resources.SHADOW_DOCUMENT), resources.SHADOW_DOCUMENT)
        # test cache full load (no change)
        self.assertDictEqual(self.mqtt.filter_delta(
            resources.SHADOW_DOCUMENT, {}), {})
        # test single value diff
        incoming = deepcopy(resources.SHADOW_DOCUMENT)
        updated = resources.SHADOW_DOCUMENT['desired']['imaging_settings']['dpc_exposure'] + 1
        incoming['desired']['imaging_settings']['dpc_exposure'] = updated
        self.assertDictEqual(self.mqtt.filter_delta(
            resources.SHADOW_DOCUMENT, incoming), {'desired': {'imaging_settings': {'dpc_exposure': updated}}})
