import asyncio
import json
import threading
from typing import Optional

from bclib.log_service.schema_base_logger import SchemaBaseLogger


class RabbitSchemaBaseLogger(SchemaBaseLogger):
    """
    RabbitMQ Schema Logger

    Logger implementation that sends formatted schema data to RabbitMQ.
    Supports both direct queue and exchange-based routing.

    Configuration:
        options['connection'] must contain:
            - url: RabbitMQ connection URL (e.g., 'amqp://guest:guest@localhost:5672/')
            - Either 'queue' (direct) or 'exchange' (routing-based)
            - Optional: passive, durable, exclusive, auto_delete flags

    Features:
        - Direct queue publishing
        - Exchange-based routing with routing keys
        - Queue declaration with configurable options
        - One reused connection per logger, guarded by a lock (pika's
          BlockingConnection is not thread-safe); reconnects and retries once
          when the connection was lost
        - Async execution via thread pool

    Example:
        ```python
        options = {
            'url': 'http://api.example.com/schema',
            'connection': {
                'url': 'amqp://localhost',
                'exchange': 'logs',
                'durable': True
            }
        }
        logger = RabbitSchemaBaseLogger(options)

        log_obj = logger.new_object_log('event', routing_key='users.login', user_id=123)
        await logger.log_async(log_obj)
        ```
    """

    def __init__(self, options: dict, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """
        Initialize RabbitMQ schema logger

        Args:
            options: Logger configuration dictionary containing:
                - connection:
                    - url: RabbitMQ connection URL
                    - queue: Queue name (for direct publishing)
                    - exchange: Exchange name (for routing-based publishing)
                    - passive: (optional) Passive queue declaration
                    - durable: (optional) Durable queue
                    - exclusive: (optional) Exclusive queue
                    - auto_delete: (optional) Auto-delete queue
            loop: Application event loop used by log_in_background

        Raises:
            Exception: If connection configuration is missing or invalid
            Exception: If both 'queue' and 'exchange' are specified
            Exception: If neither 'queue' nor 'exchange' is specified
        """
        super().__init__(options, loop)
        if "connection" not in options:
            raise Exception("connection not set in logger option.")
        self.__connection_options = options["connection"]
        if "url" not in self.__connection_options:
            raise Exception("url not set in connection option.")
        if "queue" in self.__connection_options and "exchange" in self.__connection_options:
            raise Exception("'queue' not acceptable when 'exchange' is set")
        elif "queue" not in self.__connection_options and "exchange" not in self.__connection_options:
            raise Exception(
                "'exchange' or 'queue' must be set in connection option")
        self.__lock = threading.Lock()
        self.__connection = None
        self.__channel = None

    async def _save_schema_async(self, schema: dict, routing_key: Optional[str] = None):
        """
        Save schema data to RabbitMQ

        Publishes formatted schema to RabbitMQ using either direct queue
        or exchange-based routing. Runs in a thread pool to avoid blocking
        the async event loop.

        Args:
            schema: Formatted schema data to publish
            routing_key: Routing key for exchange-based publishing

        Raises:
            Exception: If routing_key is provided for direct queue publishing
            pika exceptions: If RabbitMQ connection or publishing fails

        Note:
            Uses blocking pika client in thread pool executor for compatibility
            with asyncio.
        """
        if routing_key is not None and "queue" in self.__connection_options:
            raise Exception(
                "'routing key' is not acceptable when 'queue' is in options")

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
        queue = self.__connection_options.get("queue")
        channel.basic_publish(
            exchange=self.__connection_options.get("exchange", ""),
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
                pika.URLParameters(self.__connection_options["url"]))
            self.__channel = self.__connection.channel()
            queue = self.__connection_options.get("queue")
            if queue is not None:
                self.__channel.queue_declare(
                    queue=queue,
                    passive=self.__connection_options.get("passive", False),
                    durable=self.__connection_options.get("durable", False),
                    exclusive=self.__connection_options.get("exclusive", False),
                    auto_delete=self.__connection_options.get("auto_delete", False)
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
