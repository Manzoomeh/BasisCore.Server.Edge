import asyncio
from abc import ABC, abstractmethod
import pika
from bclib.utility import DictEx

class RabbitListener(ABC):
    def __init__(self, connection_options: DictEx) -> None:
        try:
            self.__param = pika.URLParameters(connection_options.url)
            self._host: str = self.__param.host
            self._queue_name: str = connection_options.queue
            self.__passive = connection_options.passive if connection_options.has(
                "passive") else False
            self.__durable = connection_options.durable if connection_options.has(
                "durable") else False
            self.__exclusive = connection_options.exclusive if connection_options.has(
                "exclusive") else False
            self.__auto_delete = connection_options.auto_delete if connection_options.has(
                "auto_delete") else False
            self.__retry_delay = int(
                connection_options.retry_delay) if connection_options.has("retry_delay") else 60
        except Exception as ex:
            print(f"Error in config rabbit-mq ({ex})")
            raise ex

    def __try_to_apply_connection(self):
        print("Rabbit connection attemp...")
        self.__connection = pika.BlockingConnection(self.__param)
        self.__channel = self.__connection.channel()
        self.__channel.queue_declare(
            queue=self._queue_name,
            passive=self.__passive,
            durable=self.__durable,
            exclusive=self.__exclusive,
            auto_delete=self.__auto_delete
        )
        self.__channel.basic_consume(
            queue=self._queue_name, on_message_callback=lambda channel, method, properties, body: self.on_rabbit_message_received(body), auto_ack=True)

    @abstractmethod
    def on_rabbit_message_received(self, body):
        pass

    def initialize_task(self, loop: asyncio.AbstractEventLoop) -> asyncio.Future:
        loop.create_task(self.__consuming_task())

    async def __consuming_task(self):
        while True:
            try:
                self.__try_to_apply_connection()
                print(
                    f'Rabbit listener waiting for messages from "{self._host}:{self._queue_name}."')
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.__channel.start_consuming)
                break
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
                break
            except Exception as ex:
                print(f"[{ex.__class__.__name__}]", str(ex))
            print(f"Reconnecting in {self.__retry_delay} seconds...")
            await asyncio.sleep(self.__retry_delay)
