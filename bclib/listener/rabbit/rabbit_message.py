"""Rabbit Message - Message implementation for RabbitMQ communications"""
from typing import Any, Optional

from pika import spec
from pika.adapters.blocking_connection import BlockingChannel

from bclib.listener.message import Message


class RabbitMessage(Message):
    """
    Message class for RabbitMQ communications

    This message type is used for receiving messages from RabbitMQ queues/exchanges.
    Unlike other message types, RabbitMQ messages are one-way (no response).

    Attributes:
        host: RabbitMQ server host
        queue: Queue name message was received from
        body: Raw message body as bytes
        routing_key: Routing key used (for exchange-based routing)
        channel: Pika channel object for performing operations
        method: Pika method object containing delivery information
        properties: Pika properties object containing message metadata
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
        channel: Optional[BlockingChannel] = None,
        method: Optional[spec.Basic.Deliver] = None,
        properties: Optional[spec.BasicProperties] = None,
        routing_key: Optional[str] = None
    ) -> None:
        """
        Initialize RabbitMessage

        Args:
            host: RabbitMQ server host
            queue: Queue name
            body: Raw message body as bytes
            channel: Pika channel object for performing operations
            method: Pika method object containing delivery information
            properties: Pika properties object containing message metadata
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

        # Extract commonly used fields for convenience
        self.delivery_tag = method.delivery_tag if method else None
        self.exchange = method.exchange if method else None
        self.content_type = properties.content_type if properties else None
        self.headers = dict(
            properties.headers) if properties and properties.headers else {}

    @property
    def message_text(self) -> str:
        """Get message body as UTF-8 decoded string"""
        return self.body.decode("utf-8") if self.body else ""
