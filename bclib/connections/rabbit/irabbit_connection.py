from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, TypeVar, Union

if TYPE_CHECKING:
    from aio_pika import Channel, Message, RobustConnection
    from aio_pika.abc import AbstractExchange, AbstractQueue


T = TypeVar('T')


class IRabbitConnection(Generic[T], ABC):
    """
    RabbitMQ Connection Interface - Async implementation using aio_pika.

    Use this interface for dependency injection without inheritance.
    The generic type parameter T specifies the configuration key.

    Example:
        ```python
        class NotificationService:
            def __init__(self, rabbit: IRabbitConnection['rabbitmq.notifications']):
                self.rabbit = rabbit

            async def send_notification(self, user_id: str, message: str):
                await self.rabbit.publish({'user_id': user_id, 'message': message})
        ```

    Features:
        - Fully async/await using aio_pika
        - No inheritance required
        - Type-safe configuration
        - Easy to mock in tests
        - Similar to ILogger<T> pattern
        - Auto-reconnection with robust connections
        - Support for both Queue and Exchange modes
    """

    @property
    @abstractmethod
    async def connection(self) -> 'RobustConnection':
        """Get RabbitMQ robust connection instance."""
        pass

    @abstractmethod
    async def get_channel_async(self) -> 'Channel':
        """Get RabbitMQ channel instance."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connection is active."""
        pass

    @property
    @abstractmethod
    def host(self) -> str:
        """Get RabbitMQ host address."""
        pass

    @property
    @abstractmethod
    def queue_name(self) -> Optional[str]:
        """Get queue name (None if using exchange mode)."""
        pass

    @property
    @abstractmethod
    def exchange_name(self) -> Optional[str]:
        """Get exchange name (None if using queue mode)."""
        pass

    @property
    @abstractmethod
    def routing_key(self) -> str:
        """Get routing key for exchange mode."""
        pass

    @abstractmethod
    async def connect_async(self) -> None:
        """
        Establish connection to RabbitMQ.

        This method is called automatically when needed, but can be called
        explicitly for early connection establishment.
        """
        pass

    @abstractmethod
    async def publish_async(
        self,
        message: Union[Dict[str, Any], 'Message'],
        routing_key: Optional[str] = None,
        exchange: Optional[str] = None
    ) -> None:
        """
        Publish a message to RabbitMQ.

        Args:
            message: The message to publish (dict will be JSON serialized, or aio_pika.Message for direct publish)
            routing_key: Optional routing key (for exchange mode)
            exchange: Optional exchange name (overrides config)
        """
        pass

    @abstractmethod
    async def publish_to_queue(self, message: Any, queue: Optional[str] = None) -> None:
        """
        Publish a message directly to a queue.

        Args:
            message: The message to publish
            queue: Optional queue name (overrides config)
        """
        pass

    @abstractmethod
    async def declare_queue(
        self,
        queue: str,
        durable: bool = False,
        exclusive: bool = False,
        auto_delete: bool = False
    ) -> 'AbstractQueue':
        """Declare a queue."""
        pass

    @abstractmethod
    async def declare_exchange(
        self,
        exchange: str,
        exchange_type: str = 'topic',
        durable: bool = False
    ) -> 'AbstractExchange':
        """Declare an exchange."""
        pass

    @abstractmethod
    async def bind_queue_async(
        self,
        queue: str,
        exchange: str,
        routing_key: str = ''
    ) -> None:
        """Bind a queue to an exchange."""
        pass

    @abstractmethod
    async def close_async(self) -> None:
        """Close the RabbitMQ connection."""
        pass

    @abstractmethod
    async def get_queue_async(self) -> 'AbstractQueue':
        """Get or create the configured queue."""
        pass
