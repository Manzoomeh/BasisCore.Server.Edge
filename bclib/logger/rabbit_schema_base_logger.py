import asyncio
import json
from ..logger.schema_base_logger import SchemaBaseLogger
from bclib.utility import DictEx


class RabbitSchemaBaseLogger(SchemaBaseLogger):
    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        if not options.has("connection") or not options.connection.has("url") or not options.connection.has("queue"):
            raise Exception(
                "connection part of schema logger not set.")

    async def _save_schema_async(self, schema: dict):
        def send_to_rabbit(options):
            import pika
            connection = pika.BlockingConnection(
                pika.URLParameters(options.connection.url))
            channel = connection.channel()
            channel.queue_declare(queue=options.connection.queue)
            channel = connection.channel()
            channel.basic_publish(
                exchange='', routing_key=options.connection.queue, body=json.dumps(schema))
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, send_to_rabbit, self.options)
        await future
