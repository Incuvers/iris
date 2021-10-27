#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shutdown Listener
=================
Modified: 2021-03

Dependancies
------------
```
import socket
import logging.config

from monitor.event_handler.event_handler import EventHandler
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

# import socket
# import logging.config

# from monitor.event_handler.event_handler import EventHandler

# class ShutdownHandler:

#     def __init__(self, event_handler:EventHandler) -> None:
#         self._logger = logging.getLogger(__name__)
#         self.event_handler = event_handler
#         self._logger.info("%s instantiated successfully.", __name__)

#     def shutdown_server(self):
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as soc:
#             port = 5050
#             # shutdown server socket bind
#             soc.bind(('127.0.0.1', port))
#             while True:
#                 self._logger.info("Shutdown listener active waiting for requests on port: %s", port)
#                 soc.listen()
#                 conn, addr = soc.accept()
#                 with conn:
#                     self._logger.info("Connected by: %s", addr)
#                     while True:
#                         request = conn.recv(1024)
#                         # check for stop command string
#                         if request.decode() == "STOP":
#                             self._logger.info("Received shutdown response: %s", request.decode())
#                             # teardown the UI
#                             self.event_handler.trigger('SNAP_STOP')
#                         else:
#                             # if EOF received the connection was severed
#                             self._logger.info("Detected EOF severing client connection")
#                             break
