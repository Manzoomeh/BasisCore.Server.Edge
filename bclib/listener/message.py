from abc import ABC

from bclib.listener.message_type import MessageType


class Message(ABC):
    """Base message class for all communication types

    This is the base class that serves as a common interface for all message types
    in the BasisCore.Server.Edge framework. Each subclass (HttpMessage, SocketMessage,
    WebSocketMessage, RabbitMessage) manages its own specific fields and behavior.

    The default message type is AD_HOC, but subclasses can override this property
    to return different message types based on their specific use case.
    """

    @property
    def type(self) -> MessageType:
        """
        Get the message type

        Returns:
            MessageType: The type of this message (default is AD_HOC)
        """
        return MessageType.AD_HOC
