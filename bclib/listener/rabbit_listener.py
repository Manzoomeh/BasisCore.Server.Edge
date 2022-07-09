import asyncio
from abc import ABC, abstractmethod
from bclib.utility import DictEx


class RabbitListener(ABC):

    def __init__(self, connection_options: DictEx) -> None:
        import pika
        try:
            param = pika.URLParameters(connection_options.url)
            self._host: str = param.host
            self._queue_name: str = connection_options.queue
            self.__connection = pika.BlockingConnection(param)
            self.__channel = self.__connection.channel()
            self.__channel.queue_declare(
                queue=self._queue_name,
                passive=connection_options.passive if connection_options.passive else False,
                durable=connection_options.durable if connection_options.durable else False,
                exclusive=connection_options.exclusive if connection_options.exclusive else False,
                auto_delete=connection_options.auto_delete if connection_options.auto_delete else False
            )

            self.__channel.basic_consume(
                queue=self._queue_name, on_message_callback=lambda channel, method, properties, body: self.on_rabbit_message_received(body), auto_ack=True)
        except Exception as ex:
            print(f"Error in config rabbit-mq ({ex})")
            raise ex

    @abstractmethod
    def on_rabbit_message_received(self, body):
        pass

    def initialize_task(self, loop: asyncio.AbstractEventLoop) -> asyncio.Future:
        loop.create_task(self.__consuming_task())

    async def __consuming_task(self):
        try:
            print(
                f'Rabbit listener waiting for messages from "{self._host}:{self._queue_name}."')
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self.__channel.start_consuming)
        except asyncio.CancelledError:
            self.__channel.stop_consuming()
            self.__channel.cancel()
            try:
                self.__channel.close()
            except:
                pass
            try:
                self.__connection.close()
            except:
                pass
