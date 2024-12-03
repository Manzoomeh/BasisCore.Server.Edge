import asyncio
import json
from typing import Optional
from ..logger.schema_base_logger import SchemaBaseLogger
from bclib.utility import DictEx


class RabbitSchemaBaseLogger(SchemaBaseLogger):
    def __init__(self, options: 'DictEx') -> None:
        super().__init__(options)
        if "connection" not in options.logger:
            raise Exception("connection not set in logger option.")
        self.__connection_options = options.logger.connection
        if "url" not in self.__connection_options:
            raise Exception("url not set in connection option.")
        if "queue" in self.__connection_options and "exchange" in self.__connection_options:
            raise Exception("'queue' not acceptable when 'exchange' is set")
        elif "queue" not in self.__connection_options and "exchange" not in self.__connection_options:
            raise Exception("'exchange' or 'queue' must be set in connection option")
        
    async def _save_schema_async(self, schema: dict, routing_key: Optional[str] = None):
        if routing_key is not None and self.__connection_options.queue is not None:
            raise Exception("'routing key' is not acceptable when 'queue' is in options")

        def send_to_rabbit():
            import pika
            connection = pika.BlockingConnection(
                pika.URLParameters(
                    self.__connection_options.url
                )
            )
            channel = connection.channel()
            queue = self.__connection_options.queue
            if queue is not None:
                channel.queue_declare(
                    queue=queue,
                    passive=self.__connection_options.passive or False,
                    durable=self.__connection_options.durable or False,
                    exclusive=self.__connection_options.exclusive or False,
                    auto_delete=self.__connection_options.auto_delete or False
                )
            channel.basic_publish(
                exchange=self.__connection_options.exchange or "", 
                routing_key=routing_key or queue or "", 
                body=json.dumps(schema, ensure_ascii=False),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    content_encoding="utf-8"
                )
            )
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, send_to_rabbit)
        await future
