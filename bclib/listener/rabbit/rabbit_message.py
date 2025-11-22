"""Rabbit Message - Message implementation for RabbitMQ communications"""
from typing import Optional

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

    Example:
        ```python
        message = RabbitMessage(
            session_id="unique_id",
            message_type=MessageType.MESSAGE,
            host="localhost",
            queue="tasks",
            body=b'{"task": "process"}',
            routing_key="task.process"
        )
        ```
    """

    def __init__(
        self,
        host: str,
        queue: str,
        body: bytes,
        routing_key: Optional[str] = None
    ) -> None:
        """
        Initialize RabbitMessage

        Args:
            host: RabbitMQ server host
            queue: Queue name
            body: Raw message body as bytes
            routing_key: Optional routing key for exchange-based routing
        """
        # RabbitMessage doesn't need session_id or type
        self.host = host
        self.queue = queue
        self.body = body
        self.routing_key = routing_key

    @property
    def message_text(self) -> str:
        """Get message body as UTF-8 decoded string"""
        return self.body.decode("utf-8") if self.body else ""
