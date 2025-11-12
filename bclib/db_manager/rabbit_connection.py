"""Restful implementation of Db wrapper"""
import json
from typing import Any, Optional

from bclib.utility import DictEx

from ..db_manager.db import Db


class RabbitConnection(Db):
    """Restful implementation of Db wrapper"""

    def __init__(self, connection_setting: DictEx) -> None:
        super().__init__()
        self.__connection_setting = connection_setting
        self.__connection = None
        self.__channel = None

        # Validate configuration similar to RabbitSchemaBaseLogger
        if "queue" in connection_setting and "exchange" in connection_setting:
            raise Exception("'queue' not acceptable when 'exchange' is set")
        elif "queue" not in connection_setting and "exchange" not in connection_setting:
            raise Exception(
                "'exchange' or 'queue' must be set in connection settings")

    def __enter__(self):
        import pika
        self.__connection = pika.BlockingConnection(
            pika.URLParameters(self.__connection_setting.url))
        self.__channel = self.__connection.channel()

        # Only declare queue if queue is specified (not when using exchange)
        queue = self.__connection_setting.queue
        if queue is not None:
            self.__channel.queue_declare(
                queue=queue,
                passive=self.__connection_setting.passive if self.__connection_setting.passive else False,
                durable=self.__connection_setting.durable if self.__connection_setting.durable else False,
                exclusive=self.__connection_setting.exclusive if self.__connection_setting.exclusive else False,
                auto_delete=self.__connection_setting.auto_delete if self.__connection_setting.auto_delete else False
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__connection is not None:
            self.__connection.close()
        return super().__exit__(exc_type, exc_val, exc_tb)

    def publish(self, message: Any, routing_key: Optional[str] = None):
        """Send message to rabbit-mq

        Args:
            message: The message to publish
            routing_key: Optional routing key (required when using exchange, not allowed with queue)
        """
        if routing_key is not None and self.__connection_setting.queue is not None:
            raise Exception(
                "'routing_key' is not acceptable when 'queue' is in settings")

        if self.__channel is not None:
            msg_json = json.dumps(message, ensure_ascii=False)

            # Use exchange or empty string, and routing_key or queue
            exchange = self.__connection_setting.exchange or ""
            final_routing_key = routing_key or self.__connection_setting.queue or ""

            self.__channel.basic_publish(
                exchange=exchange,
                routing_key=final_routing_key,
                body=msg_json,
                properties=self._get_message_properties()
            )
        else:
            raise Exception(
                f'for host {self.__connection_setting.host}, channel not created!'
            )

    def _get_message_properties(self):
        """Get message properties for publishing"""
        import pika
        return pika.BasicProperties(
            content_type="application/json",
            content_encoding="utf-8"
        )
