import asyncio
import json

from bclib.log_service.schema_base_logger import SchemaBaseLogger


class ExchangeRabbitSchemaBaseLogger(SchemaBaseLogger):
    """
    RabbitMQ Exchange Logger (Simplified)

    Simplified RabbitMQ logger for direct queue publishing with queue declaration.
    Unlike RabbitSchemaBaseLogger, this implementation focuses on direct
    queue publishing with explicit queue declaration options.

    Configuration:
        options['connection'] must contain:
            - url: RabbitMQ connection URL
            - exchange: Exchange name (used in basic_publish, typically '')
            - queue: Queue name for declaration and routing
            - Optional: durable, passive, exclusive, auto_delete flags

    Note:
        Despite the name, this logger publishes to a direct queue (exchange='').
        The routing_key parameter is required for the _save_schema_async method.

    Example:
        ```python
        options = {
            'url': 'http://api.example.com/schema',
            'connection': {
                'url': 'amqp://localhost',
                'exchange': '',
                'queue': 'logs',
                'durable': True
            }
        }
        logger = ExchangeRabbitSchemaBaseLogger(options)

        log_obj = logger.new_object_log('event', routing_key='logs', data='test')
        await logger.log_async(log_obj)
        ```
    """

    def __init__(self, options: dict) -> None:
        """
        Initialize exchange RabbitMQ schema logger

        Args:
            options: Logger configuration dictionary containing:
                - connection:
                    - url: RabbitMQ connection URL
                    - exchange: Exchange name (typically '')
                    - queue: Queue name
                    - durable: (optional) Durable queue flag
                    - passive: (optional) Passive queue declaration
                    - exclusive: (optional) Exclusive queue flag
                    - auto_delete: (optional) Auto-delete flag

        Raises:
            Exception: If 'url' or 'exchange' is missing from connection config
        """
        super().__init__(options)
        self.__connection_options = options.get("connection", {})
        if "url" not in self.__connection_options or "exchange" not in self.__connection_options:
            raise Exception("connection part of schema logger not set.")

    async def _save_schema_async(self, schema: dict, routing_key: str):
        """
        Save schema data to RabbitMQ queue

        Declares the queue and publishes the formatted schema data.
        Runs in a thread pool to avoid blocking the async event loop.

        Args:
            schema: Formatted schema data to publish
            routing_key: Queue name to publish to (required)

        Raises:
            pika exceptions: If RabbitMQ connection or publishing fails

        Note:
            Uses blocking pika client in thread pool executor.
            Queue is declared before each publish.
        """
        def send_to_rabbit(options):
            import pika
            connection_options = options["connection"]
            queue = connection_options["queue"]
            durable = connection_options.get("durable", False)
            passive = connection_options.get("passive", False)
            exclusive = connection_options.get("exclusive", False)
            auto_delete = connection_options.get("auto_delete", False)
            connection = pika.BlockingConnection(
                pika.URLParameters(connection_options["url"]))
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=durable, passive=passive,
                                  exclusive=exclusive, auto_delete=auto_delete)
            channel = connection.channel()
            channel.basic_publish(
                exchange='', routing_key=queue, body=json.dumps(schema, ensure_ascii=False))
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, send_to_rabbit, self.options)
        await future
