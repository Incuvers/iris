# -*- coding: utf-8 -*-
"""
Rabbit MQ Client
================
Modified: 2021-10
"""

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
import logging

from monitor.logs.formatter import pformat
from monitor.amqp.conf import AMQPConf


class AMQPClient:
    def __init__(self, host: str, port: int, username:str, password:str) -> None:
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Creating rabbitmq connection to host: %s port: %s", host, port)
        credentials = PlainCredentials(
            username=username,
            password=password,
            erase_on_connect=True
        )
        connection = BlockingConnection(
            ConnectionParameters(
                host=host,
                port=port,
                virtual_host='/',
                credentials=credentials
            )
        )
        self.channel = connection.channel()
        self.channel.basic_consume(
            queue=AMQPConf.Routes.TELEMETRY,
            auto_ack=True,
            on_message_callback=self.digest_telemetry
        )
        self.channel.basic_consume(
            queue=AMQPConf.Routes.ISR,
            auto_ack=True,
            on_message_callback=self.digest_isr
        )
        self._logger.info("Instantiation successful.")

    def digest_telemetry(self, ch, method, properties, body):
        self._logger.info("ch: %s:%s | method: %s:%s | properties: %s:%s | body: %s:%s",
                          ch, type(ch), method, type(method), properties, type(properties), body, type(body))
        self._logger.info("Message payload: %s", pformat(body))

    def digest_isr(self, ch, method, properties, body) -> None:
        self._logger.info("ch: %s:%s | method: %s:%s | properties: %s:%s | body: %s:%s",
                    ch, type(ch), method, type(method), properties, type(properties), body, type(body))
        self._logger.info("Message payload: %s", pformat(body))
