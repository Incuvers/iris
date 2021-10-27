# -*- coding: utf-8 -*-
"""
Unittests for State Management
==============================
Date: 2021-05

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import asyncio
import logging
import unittest
from typing import Callable
from unittest.mock import AsyncMock, MagicMock, Mock, call, patch

from monitor.models.icb import ICB
from monitor.models.experiment import Experiment
from monitor.models.imaging_profile import ImagingProfile
from monitor.models.protocol import Protocol
from monitor.models.device import Device
from monitor.environment.registry import CallbackRegistry as cr
from monitor.environment.cache import SystemCache
# mock class variable declarations before import
from monitor.environment.state_manager import StateManager
from monitor.tests.resources import models, icb


def cm_wrapper(test_case: Callable) -> Callable:
    """
    Context manager wrapper to reduce duplication in test cases

    :param test_case: test case function 
    :type test_case: Callable
    :return: wrapper for test case
    :rtype: Callable
    """

    def wrapper(self, *args, **kwargs):
        with StateManager() as state:
            test_case(self, state, *args, **kwargs)
    return wrapper


class TestState(unittest.TestCase):

    def setUp(self) -> None:
        logging.disable()

    def tearDown(self) -> None:
        logging.disable(logging.NOTSET)

    @cm_wrapper
    def test_device(self, state: StateManager):
        """
        Test device state variable checkout is a deepcopy and exception handles

        :param state: state manager instance
        :type state: StateManager
        """
        # test sanity
        new_device = Mock(spec=Device)
        new_device.configure_mock(**models.DEVICE_MODEL)
        state.device = new_device
        self.assertTrue(new_device is not state.device)

    @cm_wrapper
    def test_protocol(self, state: StateManager):
        """
        Test protocol state variable checkout is a deepcopy and exception handles

        :param state: state manager instance
        :type state: StateManager
        """
        # test sanity
        new_protocol = Mock(spec=Protocol)
        new_protocol.configure_mock(**models.PROTOCOL_MODEL)
        state.protocol = new_protocol
        self.assertTrue(new_protocol is not state.protocol)

    @cm_wrapper
    def test_imaging_profile(self, state: StateManager):
        """
        Test imaging profile state variable checkout is a deepcopy and exception handles

        :param state: state manager instance
        :type state: StateManager
        """
        # test sanity
        new_ip = Mock(spec=ImagingProfile)
        new_ip.configure_mock(**models.IMAGING_PROFILE_MODEL)
        state.imaging_profile = new_ip
        self.assertTrue(new_ip is not state.imaging_profile)

    @cm_wrapper
    def test_experiment(self, state: StateManager):
        """
        Test experiment state variable checkout is a deepcopy and exception handles

        :param state: state manager instance
        :type state: StateManager
        """
        # test sanity
        new_exp = Mock(spec=Experiment)
        new_exp.configure_mock(**models.EXPERIMENT_SERIALIZED)
        state.experiment = new_exp
        self.assertTrue(new_exp is not state.experiment)

    @cm_wrapper
    def test_icb(self, state: StateManager):
        """
        Test icb state variable checkout is a deepcopy and is correct type

        :param state: state manager instance
        :type state: StateManager
        """
        # test sanity
        new_icb = Mock(spec=ICB)
        new_icb.configure_mock(**icb.ICB_SENSORFRAME)
        state.icb = new_icb
        self.assertTrue(new_icb is not state.icb)

    @patch.object(SystemCache, 'get_protocol')
    @patch.object(SystemCache, 'get_device')
    @patch.object(SystemCache, 'get_experiment')
    @patch.object(SystemCache, 'get_imaging_profile')
    @patch.object(StateManager, 'commit')
    @cm_wrapper
    def test_load_runtime_models(self, state: StateManager, commit: MagicMock, get_imaging_profile: MagicMock,
                                 get_experiment: MagicMock, get_device: MagicMock, get_protocol: MagicMock):
        """
        Test runtime model load from cache.

        :param state: state manager instance
        :type state: StateManager
        """
        imaging_profile = Mock(spec=ImagingProfile)
        imaging_profile.configure_mock(**models.IMAGING_PROFILE_MODEL)
        get_imaging_profile.return_value = imaging_profile
        experiment = Mock(spec=Experiment)
        experiment.configure_mock(**models.EXPERIMENT_SERIALIZED)
        get_experiment.return_value = experiment
        device = Mock(spec=Device)
        device.configure_mock(**models.DEVICE_MODEL)
        get_device.return_value = device
        protocol = Mock(spec=Protocol)
        protocol.configure_mock(**models.PROTOCOL_MODEL)
        get_protocol.return_value = protocol
        state._load_runtime_models()
        self.assertEqual(commit.call_count, 4)

    @patch.object(StateManager, '_isv_runner')
    @patch.object(StateManager, '_resolve_subscriptions')
    @patch.object(SystemCache, 'write')
    @patch.object(SystemCache, 'read_lab_id', lambda x: 1)
    @patch.object(SystemCache, 'write_lab_id')
    @cm_wrapper
    def test_commit(self, state: StateManager, write_lab_id: MagicMock, cache_write: MagicMock,
                    _resolve_subscriptions: MagicMock, mock_isvr: MagicMock):
        """
        Test state variable commit and exception handling

        :param state: state manager instance
        :type state: StateManager
        :param mock_sr: mocked subscribe runner (note: async not awaited)
        :type mock_sr: AsyncMock
        :param mock_isvr: mocked isv runner 
        :type mock_isvr: MagicMock
        """
        # test committing uninitialized state variable
        uninitialized_model = Mock(spec=ImagingProfile)
        uninitialized_model.initialized = False
        self.assertFalse(state.commit(uninitialized_model))
        # cache write mock
        for state_type in [Protocol, Device, ImagingProfile, Experiment, ICB]:
            with self.subTest("Testing {} commit".format(state_type)):
                mock_state = Mock(spec=state_type)
                if state_type is Device:
                    ref = cr.device
                    mock_state.configure_mock(**models.DEVICE_MODEL)
                elif state_type is Protocol:
                    ref = cr.protocol
                    mock_state.configure_mock(**models.PROTOCOL_MODEL)
                elif state_type is ICB:
                    ref = cr.icb
                    mock_state.configure_mock(**icb.ICB_SENSORFRAME)
                elif state_type is Experiment:
                    ref = cr.experiment
                    mock_state.configure_mock(**models.EXPERIMENT_SERIALIZED)
                else:
                    ref = cr.ip
                    mock_state.configure_mock(**models.IMAGING_PROFILE_MODEL)
                self.assertTrue(state.commit(mock_state))
                _resolve_subscriptions.assert_called_once_with(mock_state, ref)
                if state_type is not ICB: cache_write.assert_called_once_with(mock_state)
                else: cache_write.assert_not_called()
                _resolve_subscriptions.reset_mock()
                cache_write.reset_mock()
                if state_type is Device:
                    write_lab_id.assert_called_with(4)
        # test isv failures and source commits
        for state_type in [ImagingProfile, ICB]:
            with self.subTest("Testing {} commit with isv failure".format(state_type)):
                mock_state = Mock(spec=state_type)
                mock_isvr.side_effect = RuntimeError
                self.assertFalse(state.commit(mock_state))
                self.assertTrue(state.commit(mock_state, source=True))

    @cm_wrapper
    def test_subscribe(self, state: StateManager):
        """
        Test subscription to state variable of designated type

        :param state: state manager instance 
        :type state: StateManager
        """
        # async defs
        async def device_callback(state: Device): ...
        async def experiment_callback(state: Experiment): ...
        async def protocol_callback(state: Protocol): ...
        async def ip_callback(state: ImagingProfile): ...
        async def icb_callback(state: ICB): ...
        # test sanity
        for state_type in [ImagingProfile, Device, Protocol, Experiment, ICB]:
            with self.subTest("Testing subscribe to state of type: {}".format(state_type)):
                if state_type is Protocol:
                    reg = cr.protocol
                    awaitable = protocol_callback
                elif state_type is Experiment:
                    reg = cr.experiment
                    awaitable = experiment_callback
                elif state_type is Device:
                    reg = cr.device
                    awaitable = device_callback
                elif state_type is ICB:
                    reg = cr.icb
                    awaitable = icb_callback
                else:
                    reg = cr.ip
                    awaitable = ip_callback
                state.subscribe(state_type, awaitable)
                self.assertEqual(reg[-1], awaitable)

    @cm_wrapper
    def test_subscribe_isv(self, state: StateManager):
        """
        Test isv subscription to state variable of designated type

        :param state: state manager instance 
        :type state: StateManager
        """
        # validator defs
        def ip_isv_callback(state: ImagingProfile) -> bool: ...
        def icb_isv_callback(state: ICB) -> bool: ...
        # test sanity
        for state_type in [ImagingProfile, ICB]:
            with self.subTest("Testing isv subscribe to state of type: {}".format(state_type)):
                if state_type is ICB:
                    reg = cr.icb_isv
                    validator = icb_isv_callback
                else:
                    reg = cr.ip_isv
                    validator = ip_isv_callback
                state.subscribe_isv(state_type, validator)
                self.assertEqual(reg[0], validator)

    @cm_wrapper
    def test_isv_runner(self, state: StateManager):
        """
        Test synchronous isv runner and exception handling

        :param state: state manager instance
        :type state: StateManager
        """
        # test None case
        real_icb = ICB()
        state._isv_runner(real_icb, [])
        # test sanity
        icb_isv_callback = Mock(return_value=True)
        cr.icb_isv.insert(0, icb_isv_callback)
        state._isv_runner(real_icb, cr.icb_isv)
        icb_isv_callback.assert_called_once_with(real_icb)
        icb_isv_callback.reset_mock()
        # test failure
        icb_isv_callback = Mock(return_value=False)
        cr.icb_isv.insert(0, icb_isv_callback)
        with self.assertRaises(RuntimeError):
            state._isv_runner(real_icb, cr.icb_isv)
        icb_isv_callback.assert_called_once_with(real_icb)
        icb_isv_callback.reset_mock()
        # any exception will do here
        icb_isv_callback = Mock(side_effect=OSError)
        cr.icb_isv.insert(0, icb_isv_callback)
        with self.assertRaises(RuntimeError):
            state._isv_runner(real_icb, cr.icb_isv)
        icb_isv_callback.assert_called_once_with(real_icb)

    @cm_wrapper
    def test_subscriber_runner(self, state: StateManager):
        """
        Test asynchronous subscriber runner.

        :param state: state manager instance
        :type state: StateManager
        """
        func_mock = Mock()
        async def func(icb: ICB) -> None: func_mock()
        async def exc_raise(icb: ICB) -> None: func_mock(side_effect=Exception)
        reg = [func, exc_raise]
        asyncio.run(state._subscriber_runner(ICB(), reg))
        func_mock.assert_has_calls(
            [
                call(),
                call(side_effect=Exception)
            ]
        )
