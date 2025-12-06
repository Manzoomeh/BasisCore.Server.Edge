"""Listener Factory Interface"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ilistener import IListener


class IListenerFactory(ABC):
    """
    Interface for creating and managing listeners based on application configuration

    Implementations should create appropriate listeners (HTTP, WebSocket, TCP, RabbitMQ)
    based on the options provided during initialization.
    """

    @abstractmethod
    def load_listeners(self) -> 'list[IListener]':
        """
        Create and return list of listeners based on configuration

        Returns:
            list[IListener]: List of configured listener instances

        Example:
            ```python
            factory = ListenerFactory(options, message_handler)
            listeners = factory.load_listeners()
            for listener in listeners:
                message_handler.add_listener(listener)
            ```
        """
        pass
