# -*- coding: utf-8 -*-
"""
Automatrix Stream Unittests
===========================
Modified: 2021-07

Dependencies:
-------------
```
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import unittest
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from monitor.microscope.automatrix.stream import AutomatrixStream


class TestAutomatrixStream(unittest.TestCase):

    def setUp(self):
        self.stream = AutomatrixStream()

    def tearDown(self):
        del self.stream

    @patch.object(AutomatrixStream, '_encode')
    def test_set_pattern(self, encode: MagicMock):
        pattern = Mock()
        encode.return_value = encoded_pattern = Mock()
        self.stream.set_pattern(pattern)
        encode.assert_called_once_with(pattern)
        self.assertEqual(self.stream.patterns[-1], encoded_pattern)

    @patch.object(AutomatrixStream, '_pattern_to_bytes')
    def test_encode(self, _pattern_to_bytes: MagicMock):
        """
        Test internal encoder

        :param _pattern_to_bytes: [description]
        :type _pattern_to_bytes: MagicMock
        """
        # test pattern exceptions
        with self.assertRaises(TypeError):
            self.stream._encode(Mock())
        with self.assertRaises(ValueError):
            self.stream._encode(np.zeros(3, np.uint8))
        with self.assertRaises(ValueError):
            self.stream._encode(np.ones((16, 16), np.uint8))
        _pattern_to_bytes.return_value = [0xff for _ in range(100)]
        with self.assertRaises(ValueError):
            self.stream._encode(np.zeros((16, 16), np.uint8))
        _pattern_to_bytes.return_value = [0xff for _ in range(32)]
        # test sanity
        self.stream._encode(np.zeros((16, 16), np.uint8))

    def test_pattern_to_bytes(self):
        """
        Test pattern to byte conversion
        """
        self.stream._pattern_to_bytes(np.zeros((16, 16), np.uint8))

    def test_get_pattern_as_array(self):
        """
        Test pattern to np.array conversion
        """
        self.stream.patterns.append(np.zeros(32, np.uint8))
        self.stream.get_pattern_as_array()

    def test_grid_to_shift_coords(self):
        """
        Test grid to SR coordinates
        """
        self.stream._grid_to_shift_coords(1, 1)

    def test_shift_to_grid_coords(self):
        """
        Test SR coordinates to grid
        """
        self.stream._shift_to_grid_coords(1, 2)
