import asyncio
from struct import error
from typing import TYPE_CHECKING, Optional

from bclib.dispatcher.imessage_handler import IMessageHandler
from bclib.listener.ilistener import IListener
from bclib.listener.message import Message
from bclib.listener.rabbit.rabbit_message import RabbitMessage
from bclib.logger.ilogger import ILogger


class RabbitListener(IListener):
    def __init__(self, message_handler: IMessageHandler, logger: ILogger['RabbitListener'], options: dict) -> None:
        self._message_handler = message_handler
        self._logger = logger
        self.__options = options

        # Extract connection options from options dict
        connection_options = options.get(
            'connection_options') or options.get('rabbit') or options

        import pika
        from pika.adapters.blocking_connection import BlockingChannel
        try:
            # Validate configuration - mutual exclusivity between queue and exchange
            if "queue" in connection_options and "exchange" in connection_options:
                # Allow queue name with exchange when auto_queue is False
                if "auto_queue" in connection_options and not connection_options["auto_queue"]:
                    # Queue name is allowed with exchange when auto_queue=False
                    pass
                else:
                    raise Exception(
                        "'queue' not acceptable when 'exchange' is set (unless auto_queue=False)")
            elif "queue" not in connection_options and "exchange" not in connection_options:
                raise Exception(
                    "'exchange' or 'queue' must be set in connection settings")

            self.__param = pika.URLParameters(connection_options["url"])
            self._host: str = self.__param.host

            # Queue or Exchange configuration
            self._queue_name: Optional[str] = connection_options.get("queue")
            self._exchange_name: Optional[str] = connection_options.get(
                "exchange")
            self._routing_key: str = connection_options.get("routing_key", "")

            # Exchange type (default to 'topic' for flexibility)
            self._exchange_type: str = connection_options.get(
                "exchange_type", "topic")

            # Queue declaration settings
            self.__passive: bool = connection_options.get("passive", False)
            self.__durable: bool = connection_options.get("durable", False)
            self.__exclusive: bool = connection_options.get("exclusive", False)
            self.__auto_delete: bool = connection_options.get(
                "auto_delete", False)

            # Exchange-specific: Use auto-generated queue name or specified one
            self._use_auto_queue: bool = connection_options.get(
                "auto_queue", True)

            # Validate: if auto_queue=False with exchange, we need either queue name or will use default
            if self._exchange_name and not self._use_auto_queue and "queue" not in connection_options:
                if self._logger:
                    self._logger.warning(
                        f"Using default queue name '{self._exchange_name}_queue' for exchange '{self._exchange_name}'")

            self.__retry_delay: int = int(
                connection_options.get("retry_delay", 60))

            # Will store the actual queue name used for consuming
            self.__consuming_queue_name: Optional[str] = None

            # Connection and channel objects
            self.__connection: Optional[pika.BlockingConnection] = None
            self.__channel: Optional[BlockingChannel] = None
            # Store event loop reference for cross-thread task scheduling
            self.__event_loop: Optional[asyncio.AbstractEventLoop] = None

        except Exception as ex:
            if self._logger:
                self._logger.error(f"Error in config rabbit-mq ({ex})")
            raise ex

    def __try_to_apply_connection(self):
        if self._logger:
            self._logger.info("Rabbit connection attempt...")
        import pika
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

            if self._logger:
                self._logger.info(
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
            on_message_callback=self.__on_message_callback_sync,
            auto_ack=True
        )

    def __on_message_callback_sync(self, channel, method, properties, body):
        """Synchronous callback wrapper that schedules the async handler"""
        if self.__event_loop:
            asyncio.run_coroutine_threadsafe(
                self.on_rabbit_message_received_async(
                    channel, method, properties, body),
                self.__event_loop
            )

    async def on_rabbit_message_received_async(self, channel, method, properties, body):
        try:
            # Create RabbitMessage with all pika objects
            message = RabbitMessage(
                host=self._host,
                queue=self._queue_name,
                body=body,
                channel=channel,
                method=method,
                properties=properties,
                routing_key=self._routing_key if hasattr(
                    self, '_routing_key') else None
            )
            await self._message_handler.on_message_receive_async(message)
        except error as ex:
            if self._logger:
                self._logger.error(
                    f"error in dispatcher received message from rabbit in {self._host}:{self._queue_name} ({ex})")

    def initialize_task(self, loop: asyncio.AbstractEventLoop) -> asyncio.Future:
        self.__event_loop = loop
        return loop.create_task(self.__consuming_task())

    async def __consuming_task(self):
        while True:
            try:
                self.__try_to_apply_connection()

                target_info = f"{self._exchange_name} (routing key: {self._routing_key})" if self._exchange_name else self._queue_name
                if self._logger:
                    self._logger.info(
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
                if self._logger:
                    self._logger.error(f"[{ex.__class__.__name__}] {str(ex)}")
            if self._logger:
                self._logger.info(
                    f"Reconnecting in {self.__retry_delay} seconds...")
            await asyncio.sleep(self.__retry_delay)
