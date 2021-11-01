from typing import Callable
import pika
import json
import asyncio
from .signaler import Signaler


class RabbitSignaller(Signaler):
    """Implement rabbit-mq signaler"""

    def __init__(self, options: dict, callback: Callable[[list], None]) -> None:
        super().__init__(options, callback)
        try:
            host = options["host"]
            queue_name = options["queue"]
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host))
            channel = connection.channel()
            channel.queue_declare(queue=queue_name)

            def on_rabbit_message_received(ch, method, properties, body):
                print(f"Message received from {host}:{queue_name} ({body})")
                try:
                    cmd = json.loads(body)
                    if cmd and "type" in cmd:
                        cmd_type = cmd["type"]
                        if cmd_type == "clear-cache" and "keys" in cmd:
                            keys = cmd["keys"]
                            self._callback(keys)

                except Exception as ex:
                    print(
                        f"error in process received message from rabbit in {host}:{queue_name} ({ex})")

            channel.basic_consume(
                queue=queue_name, on_message_callback=on_rabbit_message_received, auto_ack=True)

            print('Waiting for messages from host}:{queue_name}.')
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, channel.start_consuming)
        except Exception as ex:
            print(f"Error in config rabbit-mq ({ex})")
            raise ex
