import asyncio
from abc import abstractmethod
from typing import Awaitable, Callable, Optional

import pika

from bclib.listener.ilistener import IListener
from bclib.listener.message import Message
from bclib.utility import DictEx


class RabbitListener(IListener):
    def __init__(self, connection_options: DictEx, async_callback: Callable[[Message], Awaitable[Message]]) -> None:
        super().__init__(async_callback)
        try:
            # Validate configuration - mutual exclusivity between queue and exchange
            if connection_options.has("queue") and connection_options.has("exchange"):
                # Allow queue name with exchange when auto_queue is False
                if connection_options.has("auto_queue") and not connection_options.auto_queue:
                    # Queue name is allowed with exchange when auto_queue=False
                    pass
                else:
                    raise Exception(
                        "'queue' not acceptable when 'exchange' is set (unless auto_queue=False)")
            elif not connection_options.has("queue") and not connection_options.has("exchange"):
                raise Exception(
                    "'exchange' or 'queue' must be set in connection settings")

            self.__param = pika.URLParameters(connection_options.url)
            self._host: str = self.__param.host

            # Queue or Exchange configuration
            self._queue_name: Optional[str] = connection_options.queue if connection_options.has(
                "queue") else None
            self._exchange_name: Optional[str] = connection_options.exchange if connection_options.has(
                "exchange") else None
            self._routing_key: str = connection_options.routing_key if connection_options.has(
                "routing_key") else ""

            # Exchange type (default to 'topic' for flexibility)
            self._exchange_type: str = connection_options.exchange_type if connection_options.has(
                "exchange_type") else "topic"

            # Queue declaration settings
            self.__passive: bool = connection_options.passive if connection_options.has(
                "passive") else False
            self.__durable: bool = connection_options.durable if connection_options.has(
                "durable") else False
            self.__exclusive: bool = connection_options.exclusive if connection_options.has(
                "exclusive") else False
            self.__auto_delete: bool = connection_options.auto_delete if connection_options.has(
                "auto_delete") else False

            # Exchange-specific: Use auto-generated queue name or specified one
            self._use_auto_queue: bool = connection_options.auto_queue if connection_options.has(
                "auto_queue") else True

            # Validate: if auto_queue=False with exchange, we need either queue name or will use default
            if self._exchange_name and not self._use_auto_queue and not connection_options.has("queue"):
                print(
                    f"Warning: Using default queue name '{self._exchange_name}_queue' for exchange '{self._exchange_name}'")

            self.__retry_delay: int = int(
                connection_options.retry_delay) if connection_options.has("retry_delay") else 60

            # Will store the actual queue name used for consuming
            self.__consuming_queue_name: Optional[str] = None

            # Connection and channel objects
            self.__connection: Optional[pika.BlockingConnection] = None
            self.__channel: Optional[pika.channel.Channel] = None

        except Exception as ex:
            print(f"Error in config rabbit-mq ({ex})")
            raise ex

    def __try_to_apply_connection(self):
        print("Rabbit connection attemp...")
        self.__connection = pika.BlockingConnection(self.__param)
        self.__channel = self.__connection.channel()

        if self._exchange_name is not None:
            # Exchange-based configuration
            self.__channel.exchange_declare(
                exchange=self._exchange_name,
                exchange_type=self._exchange_type,
                durable=self.__durable
            )

            # Declare queue (auto-generated or specific name)
            if self._use_auto_queue:
                # Let RabbitMQ generate a unique queue name
                result = self.__channel.queue_declare(
                    queue='',
                    exclusive=True,
                    auto_delete=True
                )
                self.__consuming_queue_name = result.method.queue
            else:
                # Use a specific queue name (from queue setting if provided)
                queue_name = self._queue_name if self._queue_name else f"{self._exchange_name}_queue"
                self.__channel.queue_declare(
                    queue=queue_name,
                    passive=self.__passive,
                    durable=self.__durable,
                    exclusive=self.__exclusive,
                    auto_delete=self.__auto_delete
                )
                self.__consuming_queue_name = queue_name

            # Bind queue to exchange
            self.__channel.queue_bind(
                exchange=self._exchange_name,
                queue=self.__consuming_queue_name,
                routing_key=self._routing_key
            )

            print(
                f"Bound queue '{self.__consuming_queue_name}' to exchange '{self._exchange_name}' with routing key '{self._routing_key}'")

        else:
            # Queue-based configuration (original behavior)
            self.__channel.queue_declare(
                queue=self._queue_name,
                passive=self.__passive,
                durable=self.__durable,
                exclusive=self.__exclusive,
                auto_delete=self.__auto_delete
            )
            self.__consuming_queue_name = self._queue_name

        # Set up consumer
        self.__channel.basic_consume(
            queue=self.__consuming_queue_name,
            on_message_callback=lambda channel, method, properties, body: self.on_rabbit_message_received(
                body),
            auto_ack=True
        )

    @abstractmethod
    def on_rabbit_message_received(self, body):
        pass

    def initialize_task(self, loop: asyncio.AbstractEventLoop) -> asyncio.Future:
        return loop.create_task(self.__consuming_task())

    async def __consuming_task(self):
        while True:
            try:
                self.__try_to_apply_connection()

                target_info = f"{self._exchange_name} (routing key: {self._routing_key})" if self._exchange_name else self._queue_name
                print(
                    f'Rabbit listener waiting for messages from "{self._host}:{target_info}"')

                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, self.__channel.start_consuming)
                break
            except asyncio.CancelledError:
                if self.__channel is not None:
                    self.__channel.stop_consuming()
                    self.__channel.cancel()
                    try:
                        self.__channel.close()
                    except:
                        pass
                if self.__connection is not None:
                    try:
                        self.__connection.close()
                    except:
                        pass
                break
            except Exception as ex:
                print(f"[{ex.__class__.__name__}]", str(ex))
            print(f"Reconnecting in {self.__retry_delay} seconds...")
            await asyncio.sleep(self.__retry_delay)
