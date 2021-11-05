# -*- coding: utf-8 -*-
"""
Unittests for Setpoint Scheduler
================================
Modified: 2021-07

Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import math
import asyncio
import unittest
import freezegun
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, call, patch

from tests.resources import models
from monitor.models.experiment import Experiment
from monitor.scheduler.scheduler import Scheduler
from monitor.scheduler.imaging import ImagingScheduler
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import StateManager


class TestImaging(unittest.TestCase):

    @patch.object(StateManager, '__enter__')
    @patch.object(Scheduler, '__init__', lambda x: None)
    def setUp(self, _: MagicMock) -> None:
        self.imaging = ImagingScheduler()
        self.imaging._logger = Mock()

    def tearDown(self) -> None:
        del self.imaging

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
        # test experiment event (future)
        experiment = Mock(spec=Experiment)
        experiment.configure_mock(**models.EXPERIMENT_MODEL)
        print(experiment.image_capture_interval)
        with freezegun.freeze_time(datetime.fromisoformat(
                models.EXPERIMENT_SERIALIZED['start_at']) - timedelta(hours=1, minutes=0)):
            asyncio.run(self.imaging._schedule(experiment))
        start = math.ceil(experiment.start_at.timestamp())
        calls = []
        delta = start
        while delta < experiment.end_at.timestamp():
            calls.append(call(delta, 0, events.capture_pipeline.begin))
            delta += experiment.image_capture_interval * 60
        populate.assert_has_calls(calls, any_order=False)
        purge.assert_called_once()
        populate.reset_mock()
        purge.reset_mock()
        # test scheduling (active)
        self.imaging.id = None
        experiment = Mock(spec=Experiment)
        experiment.configure_mock(**models.EXPERIMENT_MODEL)
        freeze = experiment.start_at
        with freezegun.freeze_time(freeze):
            asyncio.run(self.imaging._schedule(experiment))
        calls = []
        delta = start
        while delta < experiment.end_at.timestamp():
            if delta >= start:
                calls.append(call(delta, 0, events.capture_pipeline.begin))
                delta += experiment.image_capture_interval * 60
        populate.assert_has_calls(calls, any_order=False)

    @patch.object(Scheduler, 'purge_queue')
    def test_cleanup(self, purge: MagicMock):
        """
        Test scheduler purge on experiment completion

        :param purge: [description]
        :type purge: MagicMock
        """
        experiment = Mock(spec=Experiment)
        experiment.configure_mock(**models.EXPERIMENT_MODEL)
        # experiment.active = False
        # test experiment
        asyncio.run(self.imaging.cleanup(experiment))
        purge.assert_called_once()
        # purge.reset_mock()
        # experiment.active = True
        # asyncio.run(self.imaging.cleanup(experiment))
        # purge.assert_not_called()
