# -*- coding: utf-8 -*-
"""
Unittest for Proxy Cache
========================
Date: 2021-05

Dependencies:
-------------
```
import unittest
from unittest.mock import Mock
from monitor.api.cache import ProxyCache
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import unittest

from functools import partial
from unittest.mock import Mock
from monitor.api.cache import ProxyCache


class TestProxyCache(unittest.TestCase):

    def setUp(self):
        self.proxy_cache = ProxyCache()

    def tearDown(self):
        del self.proxy_cache

    def test_cache(self):
        """ Test function caching """
        fn = Mock(return_value=None)
        function_hash = fn.__hash__()
        args = (1, 2, 3)
        self.proxy_cache.cache(fn, *args)
        # hash the passed function and validate that hash is stored in the cache correctly
        self.assertIsInstance(self.proxy_cache._proxy_buffer.get(function_hash), partial)
        self.assertEqual(self.proxy_cache._proxy_buffer[function_hash].func, fn)
        self.assertEqual(self.proxy_cache._proxy_buffer[function_hash].args, args)

    def test_exec_cached(self):
        """ Test cache execution and exception handling """
        # append a mock function to the cache. The mock function is wrapped in another function
        # to avoid confliction with partials
        test_func = Mock()
        def func(msg): test_func(msg)
        self.proxy_cache.cache(func, "test")
        self.proxy_cache.execute()
        test_func.assert_called_once_with("test")
        # assert the request is removed from the buffer
        self.assertEqual(self.proxy_cache._proxy_buffer.get(func.__hash__()), None)
        # test execution failure
        for exc in [ConnectionError, ReferenceError, TimeoutError, KeyError]:
            with self.subTest(msg=exc):
                fn = Mock(return_value=None, side_effect=exc)
                self.proxy_cache.cache(fn, "test")
                self.proxy_cache.execute()
                self.assertNotEqual(self.proxy_cache._proxy_buffer.get(fn.__hash__()), None)
