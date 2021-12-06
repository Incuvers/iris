# -*- coding: utf-8 -*-
"""
Rabbit MQ Client
================
Modified: 2021-10
"""
import json
from typing import Any, Dict
from pika import BlockingConnection, ConnectionParameters, PlainCredentials
import logging
from monitor.events.registry import Registry as events
from monitor.environment.thread_manager import ThreadManager as tm
from monitor.logs.formatter import pformat
from monitor.amqp.conf import AMQPConf


class AMQPClient:
    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self._logger = logging.getLogger(__name__)
        events.amqp_publish.register(
            callback=self.publish,
            priority=1
        )
        credentials = PlainCredentials(
            username="microservice",
            password="microservice",
            erase_on_connect=True
        )
        self.connection = BlockingConnection(
            ConnectionParameters(
                host=host,
                port=port,
                virtual_host='/',
                credentials=credentials
            )
        )
        self._logger.info("Instantiation successful.")

    def __del__(self) -> None:
        self.connection.close()
        self._logger.info("AMQP connection closed.")

    @tm.threaded(daemon=True)
    def start(self) -> None:
        """
        Create channel connection and subscribe to channel topics
        """
        # create your channel
        self.channel = self.connection.channel()
        # subscribe to AMQP topics
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
        self._logger.info("AMQP topic subscription established with broker")
        self.channel.start_consuming()

    def publish(self, route: str, body: Dict[str, Any]) -> None:
        """
        AMQP publish endpoint

        :param route: publishing route
        :type route: str
        :param body: AMQP message body
        :type body: Dict[str, Any]
        :raises ConnectionError: if channel is not initialized
        """
        if not self.channel:
            raise ConnectionError
        self.channel.basic_publish(
            exchange=AMQPConf.EXCHANGE,
            routing_key=route,
            body=json.dumps(body)
        )
        self._logger.info("Published body to %s:\n%s", route, pformat(body))

    def digest_telemetry(self, ch, method, properties, body: bytes):
        self._logger.info("ch: %s:%s | method: %s:%s | properties: %s:%s | body: %s:%s",
                          ch, type(ch), method, type(method), properties, type(properties), body, type(body))
        payload = json.loads(body.decode('utf-8'))
        self._logger.info("Message payload: %s", pformat(payload))

    def digest_isr(self, ch, method, properties, body: bytes) -> None:
        self._logger.info("ch: %s:%s | method: %s:%s | properties: %s:%s | body: %s:%s",
                          ch, type(ch), method, type(method), properties, type(properties), body, type(body))
        payload = json.loads(body.decode('utf-8'))
        self._logger.info("Message payload: %s", pformat(payload))
