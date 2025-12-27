"""RabbitMQ Connection - Modern Async Message Queue Management

A modern, fully async architecture for RabbitMQ management using aio_pika.
Provides type-safe configuration injection through generic parameters.
No inheritance required - use directly like ILogger<T>.

Example:
    ```python
    # Use directly without inheritance (Recommended)
    class NotificationService:
        def __init__(self, rabbit: IRabbitConnection['rabbitmq.notifications']):
            self.rabbit = rabbit

        async def send_notification(self, user_id: str, message: str):
            notification = {
                'user_id': user_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            await self.rabbit.publish(notification)

    # Register in DI
    services.add_scoped_generic(IRabbitConnection, RabbitConnection)
    ```

Configuration Example:
    ```json
    {
        "rabbitmq": {
            "notifications": {
                "url": "amqp://guest:guest@localhost:5672/",
                "exchange": "notifications",
                "exchange_type": "topic",
                "routing_key": "user.notification",
                "durable": true
            },
            "tasks": {
                "url": "amqp://guest:guest@localhost:5672/",
                "queue": "task_queue",
                "durable": true
            }
        }
    }
    ```
"""

import asyncio
import json
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, TypeVar, Union
from urllib.parse import urlparse

from bclib.logger import ILogger
from bclib.options import IOptions

from .irabbit_connection import IRabbitConnection

if TYPE_CHECKING:
    from aio_pika import Channel, Message, RobustConnection
    from aio_pika.abc import AbstractExchange, AbstractQueue


T = TypeVar('T')


class RabbitConnection(IRabbitConnection[T], Generic[T]):
    """
    RabbitMQ Connection Implementation - Fully async using aio_pika.

    This is the concrete implementation of IRabbitConnection.
    Similar to Logger<T> in .NET, you don't need to inherit from this class.

    Generic type parameter TConfig specifies the configuration key to retrieve
    from IOptions during dependency injection.

    Usage:
        ```python
        # Direct injection (Recommended - ILogger style)
        class EmailService:
            def __init__(self, rabbit: IRabbitConnection['rabbitmq.emails']):
                self.rabbit = rabbit

            async def send_email(self, to: str, subject: str, body: str):
                message = {
                    'to': to,
                    'subject': subject,
                    'body': body
                }
                await self.rabbit.publish(message)

        # Or for queue-based messaging
        class TaskProcessor:
            def __init__(self, rabbit: IRabbitConnection['rabbitmq.tasks']):
                self.rabbit = rabbit

            async def queue_task(self, task_data: dict):
                await self.rabbit.publish_to_queue(task_data)
        ```

    Features:
        - Fully async/await with aio_pika
        - Type-safe configuration through generics
        - Auto-reconnection with RobustConnection
        - Support for both Queue and Exchange modes
        - Context manager support
        - No inheritance required

    Attributes:
        url (str): RabbitMQ connection URL
        queue (str): Queue name (for queue mode)
        exchange (str): Exchange name (for exchange mode)
        routing_key (str): Routing key (for exchange mode)
    """

    def __init__(self, options: IOptions['RabbitConnection[T]'], loop: asyncio.AbstractEventLoop, logger: ILogger['RabbitConnection[T]']) -> None:
        """
        Initialize RabbitMQ connection with configuration options.

        Args:
            options: Configuration options containing connection details
            loop: Event loop for async operations
            logger: Optional logger for connection operations

        Required configuration keys:
            - url: RabbitMQ connection URL (amqp://...)

        Queue mode requires:
            - queue: Queue name

        Exchange mode requires:
            - exchange: Exchange name
            - routing_key: Routing key (optional, defaults to '')

        Optional configuration keys:
            - exchange_type: Exchange type (topic, direct, fanout, headers)
            - durable: Whether queue/exchange should survive server restart
            - exclusive: Queue is exclusive to this connection
            - auto_delete: Queue/exchange auto-deletes when not in use
            - passive: Don't create queue/exchange, just check if exists

        Raises:
            KeyError: If required configuration keys are missing
            ValueError: If configuration values are invalid
            Exception: If both queue and exchange are specified
        """
        self._options = options
        self._event_loop = loop
        self._logger = logger

        # Parse listener options
        self._retry_delay: int = int(self._options.get("retry_delay", 10))

        self._connection: Optional['RobustConnection'] = None
        self._channel: Optional['Channel'] = None
        self._queue: Optional['AbstractQueue'] = None
        self._exchange: Optional['AbstractExchange'] = None

        # Validate required configuration
        self._validate_options()

        # Extract common settings
        self._url = self._options['url']

        # Queue or Exchange mode
        self._queue_name: Optional[str] = self._options.get('queue')
        self._exchange_name: Optional[str] = self._options.get('exchange')
        self._routing_key: str = self._options.get('routing_key', '')

        # Exchange settings
        self._exchange_type: str = self._options.get('exchange_type', 'topic')

        # Queue/Exchange declaration settings
        self._durable: bool = self._options.get('durable', False)
        self._exclusive: bool = self._options.get('exclusive', False)
        self._auto_delete: bool = self._options.get('auto_delete', False)
        self._passive: bool = self._options.get('passive', False)

        # Parse host from URL
        parsed = urlparse(self._url)
        self._host = parsed.hostname or 'localhost'

    def _validate_options(self) -> None:
        """Validate required configuration options."""
        if 'url' not in self._options:
            raise KeyError(
                "Configuration key 'url' is required for RabbitMQ connection. "
                "Please ensure your configuration contains this key."
            )

        # Validate mutual exclusivity between queue and exchange modes
        has_queue = 'queue' in self._options
        has_exchange = 'exchange' in self._options

        if has_queue and has_exchange:
            raise Exception(
                "'queue' and 'exchange' cannot both be set. "
                "Use either queue mode or exchange mode."
            )

        if not has_queue and not has_exchange:
            raise Exception(
                "Either 'queue' or 'exchange' must be set in connection settings"
            )

    @property
    async def connection(self) -> 'RobustConnection':
        """
        Get or create RabbitMQ robust connection instance (lazy initialization).

        Returns:
            RobustConnection: Active RabbitMQ connection with auto-reconnect
        """
        if self._connection is None or self._connection.is_closed:
            await self.connect_async()
        return self._connection

    async def get_channel_async(self) -> 'Channel':
        """
        Get or create RabbitMQ channel instance (lazy initialization).

        Returns:
            Channel: Active RabbitMQ channel
        """
        if self._channel is None or self._channel.is_closed:
            await self.connect_async()
        return self._channel

    @property
    def is_connected(self) -> bool:
        """
        Check if connection is active.

        Returns:
            bool: True if connected, False otherwise
        """
        return (
            self._connection is not None and
            not self._connection.is_closed
        )

    @property
    def host(self) -> str:
        """Get RabbitMQ host address."""
        return self._host

    @property
    def queue_name(self) -> Optional[str]:
        """Get queue name (None if using exchange mode with auto_queue)."""
        return self._queue_name

    @property
    def exchange_name(self) -> Optional[str]:
        """Get exchange name (None if using queue mode)."""
        return self._exchange_name

    @property
    def routing_key(self) -> str:
        """Get routing key for exchange mode."""
        return self._routing_key

    async def connect_async(self) -> None:
        """Establish connection and channel, declare queue/exchange based on mode."""
        import aio_pika

        # Create robust connection (auto-reconnect)
        self._connection = await aio_pika.connect_robust(self._url)
        self._channel = await self._connection.channel()

        # Declare resources based on connection mode
        if self._exchange_name:
            # Exchange mode: declare exchange
            self._exchange = await self._channel.declare_exchange(
                name=self._exchange_name,
                type=aio_pika.ExchangeType(self._exchange_type),
                durable=self._durable,
                passive=self._passive
            )
        elif self._queue_name:
            # Queue mode: declare queue
            self._queue = await self._channel.declare_queue(
                name=self._queue_name,
                durable=self._durable,
                exclusive=self._exclusive,
                auto_delete=self._auto_delete,
                passive=self._passive
            )

    async def publish_async(
        self,
        message: Union[Dict[str, Any], 'Message'],
        routing_key: Optional[str] = None,
        exchange: Optional[str] = None
    ) -> None:
        """
        Publish a message to RabbitMQ with automatic JSON serialization.

        Args:
            message: The message to publish (dict will be JSON serialized, or aio_pika.Message for direct publish)
            routing_key: Optional routing key (overrides config)
            exchange: Optional exchange name (overrides config)

        Example:
            ```python
            # Exchange mode with routing key (dict)
            await rabbit.publish({'event': 'user.created', 'user_id': 123}, routing_key='user.new')

            # Direct queue publish (dict)
            await rabbit.publish({'task': 'process_data', 'id': 456})

            # Using aio_pika.Message directly
            import aio_pika
            msg = aio_pika.Message(body=b'raw data', content_type='application/octet-stream')
            await rabbit.publish(msg)
            ```
        """
        import aio_pika

        # Ensure connection is established
        channel = await self.get_channel_async()

        # Check if message is already an aio_pika.Message
        if isinstance(message, aio_pika.Message):
            aio_message = message
        else:
            # Serialize dict to JSON
            message_body = json.dumps(
                message, ensure_ascii=False).encode('utf-8')

            # Create message with properties
            aio_message = aio_pika.Message(
                body=message_body,
                content_type='application/json',
                content_encoding='utf-8',
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT if self._durable else aio_pika.DeliveryMode.NOT_PERSISTENT
            )

        # Determine target exchange and routing key from config or parameters
        target_exchange_name = exchange or self._exchange_name
        target_routing_key = routing_key or self._routing_key or self._queue_name or ''

        # Get or declare exchange
        if target_exchange_name and not self._exchange:
            target_exchange = await channel.get_exchange(target_exchange_name)
        elif self._exchange:
            target_exchange = self._exchange
        else:
            # Use default exchange for direct queue publishing
            target_exchange = channel.default_exchange

        # Publish message
        await target_exchange.publish(
            message=aio_message,
            routing_key=target_routing_key
        )

    async def publish_to_queue(self, message: Any, queue: Optional[str] = None) -> None:
        """
        Publish a message directly to a queue.

        Args:
            message: The message to publish
            queue: Optional queue name (overrides config)

        Example:
            ```python
            await rabbit.publish_to_queue({'task': 'send_email', 'to': 'user@example.com'})
            ```
        """
        target_queue = queue or self._queue_name
        if not target_queue:
            raise ValueError(
                "Queue name must be specified either in config or as parameter")

        await self.publish_async(message, routing_key=target_queue, exchange='')

    async def declare_queue(
        self,
        queue: str,
        durable: bool = False,
        exclusive: bool = False,
        auto_delete: bool = False
    ) -> 'AbstractQueue':
        """
        Declare a queue.

        Args:
            queue: Queue name
            durable: Whether queue should survive server restart
            exclusive: Queue is exclusive to this connection
            auto_delete: Queue auto-deletes when not in use

        Returns:
            AbstractQueue: Declared queue instance
        """
        channel = await self.get_channel_async()
        return await channel.declare_queue(
            name=queue,
            durable=durable,
            exclusive=exclusive,
            auto_delete=auto_delete
        )

    async def declare_exchange(
        self,
        exchange: str,
        exchange_type: str = 'topic',
        durable: bool = False
    ) -> 'AbstractExchange':
        """
        Declare an exchange.

        Args:
            exchange: Exchange name
            exchange_type: Exchange type (topic, direct, fanout, headers)
            durable: Whether exchange should survive server restart

        Returns:
            AbstractExchange: Declared exchange instance
        """
        import aio_pika

        channel = await self.get_channel_async()
        return await channel.declare_exchange(
            name=exchange,
            type=aio_pika.ExchangeType(exchange_type),
            durable=durable
        )

    async def bind_queue_async(
        self,
        queue: str,
        exchange: str,
        routing_key: str = ''
    ) -> None:
        """
        Bind a queue to an exchange.

        Args:
            queue: Queue name
            exchange: Exchange name
            routing_key: Routing key pattern
        """
        channel = await self.get_channel_async()
        queue_obj = await channel.get_queue(queue)
        await queue_obj.bind(exchange=exchange, routing_key=routing_key)

    async def get_queue_async(self) -> 'AbstractQueue':
        """
        Get or create the configured queue.

        Returns:
            AbstractQueue: The queue instance

        Raises:
            ValueError: If no queue is configured
        """
        if not self._queue_name:
            raise ValueError("No queue configured for this connection")

        if self._queue is None:
            await self.connect_async()

        return self._queue

    async def listening_async(self):
        """
        Start listening for messages with automatic retry on failure.

        This method runs indefinitely with error handling and auto-reconnection.
        Override _on_message_received in derived classes to customize message processing logic.
        """
        queue_iter = None
        while True:
            try:
                # Ensure fresh connection (close old one if needed)
                if self.is_connected:
                    try:
                        await self.close_async()
                    except:
                        pass

                await self.connect_async()

                # Get queue
                queue = await self.get_queue_async()

                # Log connection info
                target_info = f"{self.exchange_name} (routing key: {self.routing_key})" if self.exchange_name else self.queue_name
                if self._logger:
                    self._logger.info(
                        f'Rabbit listener waiting for messages from "{self.host}:{target_info}"')

                # Consume messages using async iterator
                queue_iter = queue.iterator()
                async with queue_iter:
                    async for message in queue_iter:
                        try:
                            async with message.process():
                                await self._process_message(message)
                        except Exception as ex:
                            if self._logger:
                                self._logger.error(
                                    f"Error processing message from {self.host}:{self.queue_name} - {ex}")

                break  # Exit if consumption completes normally

            except asyncio.CancelledError:
                # Graceful shutdown - close connection synchronously if event loop is still running
                try:
                    if self._logger:
                        self._logger.info(
                            "Listener cancelled, closing connection...")
                except:
                    pass  # Ignore logging errors during shutdown

                # Try to close gracefully
                try:
                    if self.is_connected:
                        await asyncio.wait_for(self.close_async(), timeout=2.0)
                except (asyncio.TimeoutError, RuntimeError):
                    # Force close if async close fails
                    try:
                        if self._connection and not self._connection.is_closed:
                            self._connection.close()
                    except:
                        pass
                except:
                    pass

                # Re-raise to properly propagate cancellation
                raise

            except Exception as ex:
                # Log error only if event loop is still running
                try:
                    if self._logger:
                        self._logger.error(
                            f"[{ex.__class__.__name__}] {str(ex)}")
                except:
                    pass

                # Close connection
                try:
                    await self.close_async()
                except:
                    pass

            # Retry after delay (only if not cancelled)
            try:
                if self._logger:
                    try:
                        self._logger.info(
                            f"Reconnecting in {self._retry_delay} seconds...")
                    except:
                        pass  # Ignore logging errors
                await asyncio.sleep(self._retry_delay)
            except asyncio.CancelledError:
                # If cancelled during sleep, cleanup and exit
                try:
                    if self.is_connected:
                        await asyncio.wait_for(self.close_async(), timeout=2.0)
                except:
                    pass
                raise

    async def _on_message_received(self, rabbit_message):
        """
        Handle received message. Override this method in derived classes.

        Args:
            rabbit_message: RabbitMessage instance containing message data
        """
        pass

    async def _process_message(self, message):
        """
        Process a single received message.

        This method wraps the aio_pika message and calls _on_message_received.
        Override _on_message_received in derived classes to customize message processing logic.

        Args:
            message: aio_pika IncomingMessage instance
        """
        # Import here to avoid circular dependency
        from bclib.listener.rabbit.rabbit_message import RabbitMessage

        # Create RabbitMessage wrapper
        rabbit_message = RabbitMessage(
            host=self.host,
            queue=self.queue_name,
            body=message.body,
            channel=None,
            method=None,
            properties=message.properties if hasattr(
                message, 'properties') else None,
            routing_key=message.routing_key or self.routing_key
        )

        # Call overridable handler
        await self._on_message_received(rabbit_message)

    async def close_async(self) -> None:
        """
        Close the RabbitMQ connection.

        Note:
            Connection will be automatically closed when used as async context manager.
        """
        # Close channel
        if self._channel is not None:
            try:
                if not self._channel.is_closed:
                    await asyncio.wait_for(self._channel.close(), timeout=3.0)
            except (asyncio.TimeoutError, RuntimeError):
                # Event loop might be closed, ignore
                pass
            except Exception:
                # Any other error during close, just log and continue
                pass
            finally:
                self._channel = None

        # Close connection
        if self._connection is not None:
            try:
                if not self._connection.is_closed:
                    await asyncio.wait_for(self._connection.close(), timeout=3.0)
            except (asyncio.TimeoutError, RuntimeError):
                # Event loop might be closed, ignore
                pass
            except Exception:
                # Any other error during close, just log and continue
                pass
            finally:
                self._connection = None

    async def __aenter__(self):
        """Async context manager entry."""
        # Ensure connection is established
        await self.connect_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures connection cleanup."""
        await self.close_async()
        return False

    def __repr__(self) -> str:
        """String representation of the connection."""
        if self._exchange_name:
            target = f"exchange='{self._exchange_name}'"
        else:
            target = f"queue='{self._queue_name}'"
        return f"<{self.__class__.__name__} {target}>"

    def __del__(self):
        """Cleanup on object deletion - ensures connection is closed."""
        try:
            # Only try to close if we have connections and they're not already closed
            if not hasattr(self, '_connection') or self._connection is None:
                return

            if self._connection.is_closed:
                return

            # Try to get event loop, but don't fail if it's closed
            try:
                import asyncio
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, try to get the default one
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        return
                except:
                    return

            # Schedule cleanup task if loop is running
            if loop.is_running():
                try:
                    loop.create_task(self.close_async())
                except:
                    pass
        except:
            # Silently ignore any cleanup errors during deletion
            pass
