# -*- coding: utf-8 -*-
"""
Unittests for Event Pipelining 
==============================
Date: 2021-05

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
import unittest
from unittest.mock import Mock
from monitor.events.pipeline import Pipeline


class TestPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = Pipeline("TEST_PIPELINE", 2)

    def tearDown(self):
        del self.pipeline

    def test_repr(self):
        """
        Test string representation of pipeline
        """
        def first(_): return None
        def second(_): return None
        self.pipeline.stage(callback=first, index=0)
        self.pipeline.stage(callback=second, index=1)
        self.pipeline.__repr__()

    def test_stage(self):
        """
        Test pipeline staging (construction) and callback indexing
        """
        def first(_): return None
        self.pipeline.stage(callback=first, index=0)
        self.assertEqual(self.pipeline.registry[0], first)
        def second(_): return None
        self.pipeline.stage(callback=second, index=1)
        self.assertEqual(self.pipeline.registry[1], second)

    def test_begin(self):
        """
        Test pipeline execution engine and exception handling 
        """
        callback = Mock(return_value=1)
        cond_callback = Mock(return_value=None)
        test_args = (1, "test")
        # test sanity
        self.pipeline.stage(callback, index=0)
        self.pipeline.stage(cond_callback, index=1)
        self.pipeline.begin(*test_args)
        callback.assert_called_once_with(*test_args)
        # test base exception
        callback.reset_mock()
        cond_callback.reset_mock()
        callback.side_effect = Exception
        self.pipeline.begin(*test_args)
        cond_callback.assert_not_called()
