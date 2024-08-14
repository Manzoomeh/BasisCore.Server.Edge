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
            connection_options = options.connection
            queue = connection_options.queue
            durable = connection_options.durable if connection_options.has("durable") else False
            passive=connection_options.passive if connection_options.has("passive") else False
            exclusive=connection_options.exclusive if connection_options.has("exclusive") else False
            auto_delete=connection_options.auto_delete if connection_options.has("auto_delete") else False
            connection = pika.BlockingConnection(
                pika.URLParameters(connection_options.url))
            channel = connection.channel()
            channel.queue_declare(queue=queue, durable=durable, passive=passive, exclusive=exclusive, auto_delete=auto_delete)
            channel = connection.channel()
            channel.basic_publish(
                exchange='', routing_key=queue, body=json.dumps(schema, ensure_ascii=False))
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, send_to_rabbit, self.options)
        await future
