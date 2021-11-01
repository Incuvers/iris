# -*- coding: utf-8 -*-
"""
Rabbit MQ Client
================
Modified: 2021-10
"""

import pika
import logging
from monitor.logs.formatter import pformat


class RMQClient:
    def __init__(self, host: str, port: int) -> None:
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Creating rabbitmq connection to host: %s port: %s", host, port)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host,
                port=port
            )
        )
        self.channel = connection.channel()
        # always declare queue
        self.channel.queue_declare(queue='test')
        self._logger.info("queue test declared")
        self.channel.basic_consume(queue='test',
                      auto_ack=True,
                      on_message_callback=self.callback)
        self._logger.info("Instantiation successful.")

    def callback(self, ch, method, properties, body):
        self._logger.info("ch: %s:%s | method: %s:%s | properties: %s:%s | body: %s:%s",
            ch, type(ch), method, type(method), properties, type(properties), body, type(body))
        self._logger.info("Message payload: %s", pformat(body))
