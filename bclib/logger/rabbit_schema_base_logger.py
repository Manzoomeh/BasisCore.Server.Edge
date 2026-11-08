import asyncio
import json
import threading
from typing import Optional
from ..logger.schema_base_logger import SchemaBaseLogger
from bclib.utility import DictEx


class RabbitSchemaBaseLogger(SchemaBaseLogger):
    """Schema logger that publishes to RabbitMQ.

    Keeps one connection per logger, guarded by a lock (pika's BlockingConnection
    is not thread-safe), and reconnects and retries once when it was lost.
    """

    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        if "connection" not in options:
            raise Exception("connection not set in logger option.")
        self.__connection_options = options.connection
        if "url" not in self.__connection_options:
            raise Exception("url not set in connection option.")
        if "queue" in self.__connection_options and "exchange" in self.__connection_options:
            raise Exception("'queue' not acceptable when 'exchange' is set")
        elif "queue" not in self.__connection_options and "exchange" not in self.__connection_options:
            raise Exception("'exchange' or 'queue' must be set in connection option")
        self.__lock = threading.Lock()
        self.__connection = None
        self.__channel = None

    async def _save_schema_async(self, schema: dict, routing_key: Optional[str] = None):
        if routing_key is not None and self.__connection_options.queue is not None:
            raise Exception("'routing key' is not acceptable when 'queue' is in options")

        def send_to_rabbit():
            with self.__lock:
                try:
                    self.__publish(schema, routing_key)
                except Exception:
                    # Connection lost (idle timeout, broker restart, ...): reconnect once.
                    self.__close_connection()
                    self.__publish(schema, routing_key)
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, send_to_rabbit)
        await future

    def __publish(self, schema: dict, routing_key: Optional[str]):
        """Publish on the shared channel, opening it first when needed. Caller holds the lock."""
        import pika
        channel = self.__get_channel()
        queue = self.__connection_options.queue
        channel.basic_publish(
            exchange=self.__connection_options.exchange or "",
            routing_key=routing_key or queue or "",
            body=json.dumps(schema, ensure_ascii=False),
            properties=pika.BasicProperties(
                content_type="application/json",
                content_encoding="utf-8"
            )
        )

    def __get_channel(self):
        """Return the open channel, (re)connecting when needed. Caller holds the lock."""
        import pika
        if self.__connection is not None and self.__connection.is_open:
            try:
                # Process pending heartbeats / close frames so a connection the broker
                # dropped while idle is detected before publishing on it.
                self.__connection.process_data_events(time_limit=0)
            except Exception:
                self.__close_connection()
        if self.__connection is None or not self.__connection.is_open:
            self.__close_connection()
            self.__connection = pika.BlockingConnection(
                pika.URLParameters(self.__connection_options.url))
            self.__channel = self.__connection.channel()
            queue = self.__connection_options.queue
            if queue is not None:
                self.__channel.queue_declare(
                    queue=queue,
                    passive=self.__connection_options.passive or False,
                    durable=self.__connection_options.durable or False,
                    exclusive=self.__connection_options.exclusive or False,
                    auto_delete=self.__connection_options.auto_delete or False
                )
        return self.__channel

    def __close_connection(self):
        """Close the shared connection, ignoring errors. Caller holds the lock."""
        connection, self.__connection, self.__channel = self.__connection, None, None
        if connection is not None:
            try:
                if connection.is_open:
                    connection.close()
            except Exception:
                pass

    def close(self):
        """Close the RabbitMQ connection held by this logger."""
        with self.__lock:
            self.__close_connection()
