import pika
import asyncio
from abc import ABC, abstractmethod
from basiscore.utility import DictEx


class RabbitListener(ABC):

    def __init__(self, connection_options: DictEx) -> None:
        try:
            param = pika.URLParameters(connection_options.url)
            self._host: str = param.host
            self._queue_name: str = connection_options.queue
            connection = pika.BlockingConnection(param)
            self.__channel = connection.channel()
            self.__channel.queue_declare(queue=self._queue_name)

            self.__channel.basic_consume(
                queue=self._queue_name, on_message_callback=lambda channel, method, properties, body: self.on_rabbit_message_received(body), auto_ack=True)
        except Exception as ex:
            print(f"Error in config rabbit-mq ({ex})")
            raise ex

    @abstractmethod
    def on_rabbit_message_received(self, body):
        pass

    def start_listening(self):
        try:
            print(
                f'Waiting for messages from {self._host}:{self._queue_name}.')
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.__channel.start_consuming)
        except KeyboardInterrupt:
            print('Bye!')
