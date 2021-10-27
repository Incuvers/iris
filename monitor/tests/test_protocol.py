#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unittests for Protocol Handler
==============================
Date: 2020-07

Dependencies:
-------------
```
import time
import unittest
from unittest.mock import Mock, patch
from monitor.tests.resources import PROTOCOL_PAYLOAD
from monitor.protocol.protocol_handler import ProtocolHandler
from monitor.event_handler.event_handler import EventHandler
```
  
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
# import time
# import unittest
# from unittest.mock import Mock, patch
# from monitor.tests.resources import PROTOCOL_PAYLOAD
# from monitor.protocol.protocol_handler import ProtocolHandler

# class TestProtocol(unittest.TestCase):

#     def setUp(self):
#         unittest.mock.patch('monitor.scheduler.setpoint.Setpoint')
#         self.protocol_handler = ProtocolHandler(self.event_handler)

#     def tearDown(self):
#         del self.protocol_handler

#     @unittest.skip("incomplete")
#     @patch('monitor.event_handler.event_handler.EventHandler.trigger')
#     @patch('monitor.protocol.layers.ProtocolLayers.update')
#     def test_trigger_channel_update(self, mock_update, mock_trigger):
#         """  """
#         # self(PROTOCOL_PAYLOAD, 0)
#         mock_trigger.assert_called_once_with('PROTOCOL_LAYER_UPDATED', priority=0)
#         mock_update.assert_called_once()
    
#     @unittest.skip("incomplete")
#     def test_integration(self):
#         mock_setpoint_event = Mock()
#         self.event_handler.register('NEW_SETPOINT_CHANGED', mock_setpoint_event)
#         self.event_handler.trigger('FETCHED_PROTOCOL', PROTOCOL_PAYLOAD, priority=0)
#         time.sleep(1)
#         mock_setpoint_event.assert_called()


# if __name__ == '__main__':
#     unittest.main()
