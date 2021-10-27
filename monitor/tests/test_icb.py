#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unittests for ICB
=================
Date: 2021-05

Dependencies:
-------------
```
import unittest
from unittest.mock import Mock, call
from monitor.models.icb import ICB
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import random
import unittest

from freezegun.api import freeze_time
from datetime import timezone, datetime
from monitor.models.icb import ICB
from monitor.tests.resources import icb


class TestICB(unittest.TestCase):

    def setUp(self):
        """
        """
        self.icb = ICB()

    def tearDown(self):
        """
        """
        del self.icb

    def test_repr(self):
        """
        Test string repr
        """
        self.assertTrue(isinstance(self.icb.__repr__(), str))

    def test_attrs(self):
        """
        Test iterative set and get helpers
        """
        self.icb.setattrs(**icb.ICB_SENSORFRAME_2)
        self.assertDictEqual(self.icb.getattrs(), icb.ICB_SENSORFRAME_2_CONV)

    def test_initialized(self):
        """
        Test the initializer property
        """
        self.assertFalse(self.icb.initialized)
        self.icb.setattrs(**icb.ICB_SENSORFRAME_2)
        self.icb.timestamp = self.icb.generate_timestamp()
        self.assertTrue(self.icb.initialized)

    def test_temp(self):
        """
        Test temp get/set
        """
        min_temp, max_temp = self.icb.OPERATING_TEMPERATURE[0], self.icb.OPERATING_TEMPERATURE[1]
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.tc
        # test bounds as floats
        self.icb.tc = min_temp
        self.assertEqual(self.icb.tc, min_temp)
        self.icb.tc = max_temp
        self.assertEqual(self.icb.tc, max_temp)
        # test floating point resolution
        tc = random.uniform(0.0, 100.0)
        self.icb.tc = tc
        self.assertEqual(self.icb.tc, round(tc, self.icb.STORAGE_RESOLUTION))
        # test out of bound
        self.icb.tc = max_temp + 1
        self.assertNotEqual(self.icb.tc, max_temp)

    def test_rh(self):
        """
        Test rh get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.rh
        # test bounds as floats
        self.icb.rh = 0.0
        self.assertEqual(self.icb.rh, 0.0)
        self.icb.rh = 100.0
        self.assertEqual(self.icb.rh, 100.0)
        # test floating point resolution
        rh = random.uniform(0.0, 100.0)
        self.icb.rh = rh
        self.assertEqual(self.icb.rh, round(rh, self.icb.STORAGE_RESOLUTION))
        # test out of bound set
        self.icb.rh = 45000
        self.assertNotEqual(self.icb.rh, 45000)

    def test_o2(self):
        """
        Test O2 get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.oc
        # test bounds as floats
        self.icb.oc = 0.0
        self.assertEqual(self.icb.oc, 0.0)
        self.icb.oc = 100.0
        self.assertEqual(self.icb.oc, 100.0)
        # test floating point resolution
        o2 = random.uniform(0.0, 100.0)
        self.icb.oc = o2
        self.assertEqual(self.icb.oc, round(o2, self.icb.STORAGE_RESOLUTION))
        # test out of bound set
        self.icb.oc = 45000
        self.assertNotEqual(self.icb.oc, 45000)

    def test_co2(self):
        """
        Test CO2 get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.cc
        # test bounds as floats
        self.icb.cc = 0.0
        self.assertEqual(self.icb.cc, 0.0)
        self.icb.cc = 100.0
        self.assertEqual(self.icb.cc, 100.0)
        # test floating point resolution
        co2 = random.uniform(0.0, 100.0)
        self.icb.cc = co2
        self.assertEqual(self.icb.cc, round(co2, self.icb.STORAGE_RESOLUTION))
        # test out of bound set
        self.icb.cc = 45000
        self.assertNotEqual(self.icb.cc, 45000)

    def test_temp_setpoint(self):
        """
        Test temperature setpoint get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.tp
        min_temp, max_temp = self.icb.TP_RANGE[0], self.icb.TP_RANGE[1]
        # test bounds as floats
        self.icb.tp = min_temp
        self.assertEqual(self.icb.tp, min_temp)
        self.icb.tp = max_temp
        self.assertEqual(self.icb.tp, max_temp)
        # test floating point resolution
        tp = random.uniform(min_temp, max_temp)
        self.icb.tp = tp
        self.assertEqual(self.icb.tp, round(tp, self.icb.STORAGE_RESOLUTION))
        # test out of bound set
        self.icb.tp = 45000
        self.assertNotEqual(self.icb.tp, 45000)

    def test_o2_setpoint(self):
        """
        Test O2 setpoint get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.op
        min_o2, max_o2 = self.icb.OP_RANGE[0], self.icb.OP_RANGE[1]
        # test bounds as floats
        self.icb.op = min_o2
        self.assertEqual(self.icb.op, min_o2)
        self.icb.op = max_o2
        self.assertEqual(self.icb.op, max_o2)
        # test floating point resolution
        op = random.uniform(min_o2, max_o2)
        self.icb.op = op
        self.assertEqual(self.icb.op, round(op, self.icb.STORAGE_RESOLUTION))
        # test out of bound set
        self.icb.op = 45000
        self.assertNotEqual(self.icb.op, 45000)

    def test_co2_setpoint(self):
        """
        Test CO2 setpoint get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.cp
        min_co2, max_co2 = self.icb.CP_RANGE[0], self.icb.CP_RANGE[1]
        # test bounds as floats
        self.icb.cp = min_co2
        self.assertEqual(self.icb.cp, min_co2)
        self.icb.cp = max_co2
        self.assertEqual(self.icb.cp, max_co2)
        # test floating point resolution
        cp = random.uniform(min_co2, max_co2)
        self.icb.cp = cp
        self.assertEqual(self.icb.cp, round(cp, self.icb.STORAGE_RESOLUTION))
        # test out of bound set
        self.icb.cp = 45000
        self.assertNotEqual(self.icb.cp, 45000)

    def test_heat_duty(self):
        """
        Test heater duty get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.hp
        # test bounds
        self.icb.hp = 0
        self.assertEqual(self.icb.hp, 0)
        self.icb.hp = 100
        self.assertEqual(self.icb.hp, 100)
        # test random
        hp = random.randint(0, 100)
        self.icb.hp = hp
        self.assertEqual(self.icb.hp, hp)
        # test out of bound set
        self.icb.hp = 101
        self.assertNotEqual(self.icb.hp, 101)

    def test_fan_duty(self):
        """
        Test fan duty get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.fp
        # test bounds
        self.icb.fp = 0
        self.assertEqual(self.icb.fp, 0)
        self.icb.fp = 100
        self.assertEqual(self.icb.fp, 100)
        # test random
        fp = random.randint(0, 100)
        self.icb.fp = fp
        self.assertEqual(self.icb.fp, fp)
        # test out of bound set
        self.icb.fp = 101
        self.assertNotEqual(self.icb.fp, 101)

    def test_fan_speed(self):
        """
        Test fan speed get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.fc
        # test bounds
        self.icb.fc = 0
        self.assertEqual(self.icb.fc, 0)
        # test random
        fc = random.randint(0, 6000)
        self.icb.fc = fc
        self.assertEqual(self.icb.fc, fc)
        # test out of bound set
        self.icb.fc = -1
        self.assertNotEqual(self.icb.fc, -1)

    def test_cozir_temp(self):
        """
        Test cozir temperature get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.ctr
        min_temp, max_temp = self.icb.OPERATING_TEMPERATURE[0], self.icb.OPERATING_TEMPERATURE[1]
        # test bounds
        self.icb.ctr = min_temp
        self.assertEqual(self.icb.ctr, min_temp)
        self.icb.ctr = max_temp
        self.assertEqual(self.icb.ctr, max_temp)
        # test random
        ctr = random.uniform(min_temp, max_temp)
        self.icb.ctr = ctr
        self.assertEqual(self.icb.ctr, ctr)
        # test out of bound set
        self.icb.ctr = -100
        self.assertNotEqual(self.icb.ctr, -100)

    def test_temp_offset(self):
        """
        Test temperature offset get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.to
        # test random
        to = random.uniform(0, 100)
        self.icb.to = to
        self.assertEqual(self.icb.to, round(to, self.icb.STORAGE_RESOLUTION))

    def test_temp_mode(self):
        """
        Test temperature mode get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.tm
        # test random
        tm = random.randint(0, 2)
        self.icb.tm = tm
        self.assertEqual(self.icb.tm, tm)
        # test invalid mode
        self.icb.tm = 3
        self.assertNotEqual(self.icb.tm, 3)

    def test_co2_mode(self):
        """
        Test CO2 mode get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.cm
        # test random
        cm = random.randint(0, 2)
        self.icb.cm = cm
        self.assertEqual(self.icb.cm, cm)
        # test invalid mode
        self.icb.cm = 3
        self.assertNotEqual(self.icb.cm, 3)

    def test_o2_mode(self):
        """
        Test O2 mode get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.om
        # test random
        om = random.randint(0, 2)
        self.icb.om = om
        self.assertEqual(self.icb.om, om)
        # test invalid mode
        self.icb.om = 3
        self.assertNotEqual(self.icb.om, 3)

    def test_version(self):
        """
        Test version get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.iv
        # test set
        self.icb.iv = "4e2a6813"
        self.assertEqual(self.icb.iv, "4e2a6813")

    def test_timestamp(self):
        """
        Test sensorframe timestamp get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.timestamp
        ts = self.icb.generate_timestamp()
        self.icb.timestamp = ts
        self.assertEqual(self.icb.timestamp, ts)

    def test_conversion(self):
        """
        Test float and int conversion helpers
        """
        # test float to int
        _float = random.uniform(0, 100)
        self.assertEqual(self.icb.float_to_int(_float), int(
            _float * 10 ** self.icb.CONVERSION_RESOLUTION))
        # test int to float
        _int = random.randint(0, 10000)
        self.assertEqual(self.icb.int_to_float(_int), _int / 10 ** self.icb.CONVERSION_RESOLUTION)

    @freeze_time("2020-10-01")
    def test_co2_calibration_time(self):
        """
        Test calibration timestamp get/set
        """
        # test initial state
        with self.assertRaises(AttributeError):
            self.icb.ct
        self.icb.ct = self.icb.calibration_time_to_iso(
            int(datetime.now(timezone.utc).timestamp() / 60 / 60 / 12))
        set_ct = self.icb.ct
        self.assertEqual(self.icb.ct, set_ct)
        # test generate co2 calibration timestamp
        self.assertEqual(
            self.icb.generate_co2_calibration_time(),
            int(datetime.now(timezone.utc).timestamp() / 60 / 60 / 12)
        )
