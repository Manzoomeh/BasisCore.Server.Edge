"""Rabbit Message - Message implementation for RabbitMQ communications"""
from typing import Any, Optional

from bclib.listener.message import Message


class RabbitMessage(Message):
    """
    Message class for RabbitMQ communications

    This message type is used for receiving messages from RabbitMQ queues/exchanges.
    Unlike other message types, RabbitMQ messages are one-way (no response).

    Compatible with both legacy pika listeners and aio-pika connections; channel,
    method, and properties are typed as Any so pika is not required at import time.

    Attributes:
        host: RabbitMQ server host
        queue: Queue name message was received from
        body: Raw message body as bytes
        routing_key: Routing key used (for exchange-based routing)
        channel: Optional channel object (pika or aio-pika) for operations
        method: Optional delivery method / metadata object
        properties: Optional message properties / metadata object
        delivery_tag: Delivery tag for manual acknowledgment
        exchange: Exchange name the message was published to
        content_type: Message content type (e.g., 'application/json')
        headers: Message headers dictionary

    Example:
        ```python
        message = RabbitMessage(
            host="localhost",
            queue="tasks",
            body=b'{"task": "process"}',
            channel=channel,
            method=method,
            properties=properties,
            routing_key="task.process"
        )
        ```
    """

    def __init__(
        self,
        host: str,
        queue: str,
        body: bytes,
        channel: Optional[Any] = None,
        method: Optional[Any] = None,
        properties: Optional[Any] = None,
        routing_key: Optional[str] = None
    ) -> None:
        """
        Initialize RabbitMessage

        Args:
            host: RabbitMQ server host
            queue: Queue name
            body: Raw message body as bytes
            channel: Optional channel object for performing operations
            method: Optional delivery method object
            properties: Optional message properties object
            routing_key: Optional routing key for exchange-based routing
        """
        # RabbitMessage doesn't need session_id or type
        self.host = host
        self.queue = queue
        self.body = body
        self.channel = channel
        self.method = method
        self.properties = properties
        self.routing_key = routing_key

        # Extract commonly used fields for convenience (pika / aio-pika compatible)
        self.delivery_tag = getattr(method, "delivery_tag", None) if method else None
        self.exchange = getattr(method, "exchange", None) if method else None
        self.content_type = getattr(
            properties, "content_type", None) if properties else None
        headers = getattr(properties, "headers", None) if properties else None
        self.headers = dict(headers) if headers else {}

    @property
    def message_text(self) -> str:
        """Get message body as UTF-8 decoded string"""
        return self.body.decode("utf-8") if self.body else ""
