import asyncio
import json
from ..logger.schema_base_logger import SchemaBaseLogger
from bclib.utility import DictEx


class RabbitSchemaBaseLogger(SchemaBaseLogger):
    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        if options.has("connection") and options.connection.has("url") and options.connection.has("queue"):
            import pika
            self.__connection = pika.BlockingConnection(
                pika.URLParameters(options.connection.url))
            channel = self.__connection.channel()
            channel.queue_declare(queue=options.connection.queue)
            self.__queue_name = options.connection.queue

        else:
            raise Exception(
                "connection part of schema logger not set.")

    async def _save_schema_async(self, schema: dict):
        def send_to_rabbit():
            channel = self.__connection.channel()
            channel.basic_publish(
                exchange='', routing_key=self.__queue_name, body=json.dumps(schema))
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, send_to_rabbit)
        await future
