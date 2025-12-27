import asyncio
from typing import TypeVar

from bclib.connections.rabbit.rabbit_connection import RabbitConnection
from bclib.dispatcher.imessage_handler import IMessageHandler
from bclib.listener.ilistener import IListener
from bclib.logger.ilogger import ILogger
from bclib.options import IOptions

T = TypeVar('T')


class RabbitListener(RabbitConnection[T], IListener):
    """
    RabbitMQ Listener - Simplified async message consumer using aio_pika.

    Extends RabbitConnection to add listening capability through simple override.
    All connection management, publishing, and queue operations inherited from base class.

    Usage:
        ```python
        class NotificationListener(RabbitListener['rabbitmq.notifications']):
            def __init__(
                self, 
                options: IOptions['rabbitmq.notifications'],
                message_handler: IMessageHandler,
                logger: ILogger['NotificationListener'],
                loop: asyncio.AbstractEventLoop
            ):
                super().__init__(options, loop, logger)
        ```

    Architecture:
        - Inherits: All RabbitConnection functionality (connect, publish, close, etc.)
        - Adds: Message consumption with retry logic
        - Override: _on_message_received() for custom message handling

    Features:
        - Fully async message consumption with aio_pika
        - Auto-reconnection with configurable retry delay
        - Clean separation: Connection in base, Listening in derived
        - No code duplication - reuses all base class methods
    """

    def __init__(
        self,
        options: IOptions[T],
        message_handler: IMessageHandler,
        logger: ILogger['RabbitListener'],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        """
        Initialize RabbitListener with connection options.

        Args:
            options: RabbitMQ connection configuration options
            message_handler: Handler for processing received messages
            logger: Logger for listener operations
            loop: Event loop for async operations
        """
        super().__init__(options, loop, logger)
        self._message_handler = message_handler

    async def _on_message_received(self, rabbit_message):
        """
        Handle received message. Override this method in derived classes.

        Args:
            rabbit_message: RabbitMessage instance containing message data
        """
        # Dispatch to message handler
        await self._message_handler.on_message_receive_async(rabbit_message)

    def initialize_task(self) -> asyncio.Future:
        """Initialize listener task on event loop."""
        return self._event_loop.create_task(self.listening_async())
