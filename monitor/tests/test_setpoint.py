# -*- coding: utf-8 -*-
"""
Unittests for Setpoint Scheduler
================================
Date: 2021-06

Dependencies:
-------------
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import math
import asyncio
import freezegun
import unittest
from datetime import datetime, timedelta
from monitor.tests import resources
from monitor.models.icb import ICB
from monitor.models.experiment import Experiment
from monitor.models.protocol import Protocol
from monitor.environment.state_manager import StateManager
from monitor.scheduler.scheduler import Scheduler
from unittest.mock import MagicMock, Mock, call, patch
from monitor.scheduler.setpoint import SetpointScheduler


class TestSetpoint(unittest.TestCase):

    @patch.object(StateManager, '__enter__')
    @patch.object(Scheduler, '__init__', lambda x: None)
    def setUp(self, _: MagicMock) -> None:
        self.setpoint = SetpointScheduler()
        self.setpoint._logger = Mock()

    def tearDown(self) -> None:
        del self.setpoint

    @patch.object(Scheduler, 'purge_queue')
    @patch.object(Scheduler, 'populate')
    def test_schedule(self, populate: MagicMock, purge: MagicMock):
        """
        Test scheduler population

        :param populate: [description]
        :type populate: MagicMock
        :param purge: [description]
        :type purge: MagicMock
        """
        # test protocol event (future)
        protocol = Mock()
        protocol.configure_mock(**resources.PROTOCOL_MODEL)
        with freezegun.freeze_time(datetime.fromisoformat(
                resources.PROTOCOL_PAYLOAD['start_at']) - timedelta(hours=1, minutes=0)):
            asyncio.run(self.setpoint.schedule(protocol))
        sps = protocol.setpoints
        start = math.ceil(protocol.start_at.timestamp())
        calls = []
        delta = start
        for _ in range(protocol.repeats):
            for sp in sps:
                calls.append(call(delta, 0, self.setpoint._trigger))
                delta += sp['duration']
                calls.append(call(delta, 0, self.setpoint.setpoint_complete))
        populate.assert_has_calls(calls, any_order=False)
        purge.assert_called_once()
        populate.reset_mock()
        purge.reset_mock()
        # test new_setpoint decorator (triggering subscription update on active protocol)
        asyncio.run(self.setpoint.schedule(protocol))
        purge.assert_not_called()
        # test scheduling (active)
        self.setpoint.id = None
        protocol = Mock()
        protocol.configure_mock(**resources.PROTOCOL_MODEL)
        with freezegun.freeze_time(datetime.fromisoformat(
                resources.PROTOCOL_PAYLOAD['start_at']) + timedelta(hours=1, minutes=10)):
            asyncio.run(self.setpoint.schedule(protocol))
            populate.assert_called()
        calls = []
        delta = start
        for _ in range(protocol.repeats):
            for sp in sps:
                if delta > start or (delta + sp['duration']) > start:
                    calls.append(call(delta, 0, self.setpoint._trigger))
                    delta += sp['duration']
                    calls.append(call(delta, 0, self.setpoint.setpoint_complete))
        populate.assert_has_calls(calls, any_order=False)

    @patch.object(StateManager, '__enter__')
    def test_setpoint_complete(self, state: MagicMock):
        """
        Test protocol progression

        :param state: [description]
        :type state: MagicMock
        """
        state.return_value.protocol = Protocol()
        state.return_value.protocol.setattrs(**resources.PROTOCOL_PAYLOAD)
        state.return_value.protocol.setpoint_index = 0
        state.return_value.protocol.repeats = 2
        self.setpoint.setpoint_complete()
        self.assertEqual(state.return_value.protocol.setpoint_index, 1)
        self.setpoint.setpoint_complete()
        self.assertEqual(state.return_value.protocol.setpoint_index, 2)
        self.setpoint.setpoint_complete()
        self.assertEqual(state.return_value.protocol.setpoint_index, 0)
        self.assertEqual(state.return_value.protocol.repeats, 1)
        self.setpoint.setpoint_complete()
        self.assertEqual(state.return_value.protocol.setpoint_index, 1)
        self.setpoint.setpoint_complete()
        self.assertEqual(state.return_value.protocol.setpoint_index, 2)
        self.setpoint.setpoint_complete()
        self.assertEqual(self.setpoint.id, None)

    @patch.object(StateManager, '__enter__')
    def test_trigger(self, state: MagicMock):
        """
        Test setpoint event triggers

        :param state: [description]
        :type state: MagicMock
        """
        state.return_value.protocol = Protocol()
        state.return_value.protocol.setattrs(**resources.PROTOCOL_PAYLOAD)
        cp = resources.PROTOCOL_PAYLOAD['setpoints'][2]['CP']
        op = resources.PROTOCOL_PAYLOAD['setpoints'][2]['OP']
        tp = resources.PROTOCOL_PAYLOAD['setpoints'][2]['TP']
        state.return_value.protocol.setpoint_index = 2
        state.return_value.icb = ICB()
        self.setpoint._trigger()
        self.assertEqual(state.return_value.icb.cp, cp)
        self.assertEqual(state.return_value.icb.tp, tp)
        self.assertEqual(state.return_value.icb.op, op)

    @patch.object(Scheduler, 'purge_queue')
    def test_complete_experiment(self, purge: MagicMock):
        """
        Test scheduler purge on experiment completion

        :param purge: [description]
        :type purge: MagicMock
        """
        experiment = Mock(spec=Experiment)
        experiment.active = False
        # test experiment
        asyncio.run(self.setpoint.complete_experiment(experiment))
        purge.assert_called_once()
        purge.reset_mock()
        experiment.active = True
        asyncio.run(self.setpoint.complete_experiment(experiment))
        purge.assert_not_called()
