"""Listener Factory Interface"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.dispatcher import IDispatcher
    from bclib.listener import IListener


class IListenerFactory(ABC):
    """
    Interface for creating and managing listeners based on application configuration

    Implementations should create appropriate listeners (HTTP, WebSocket, TCP, RabbitMQ)
    based on the options provided during initialization.
    """

    @abstractmethod
    def load_listeners(self, dispatcher: 'IDispatcher') -> 'list[IListener]':
        """
        Create and return list of listeners based on configuration

        Args:
            dispatcher: Dispatcher instance for message handling

        Returns:
            list[IListener]: List of configured listener instances

        Example:
            ```python
            factory = ListenerFactory(options)
            listeners = factory.load_listeners(dispatcher)
            for listener in listeners:
                dispatcher.add_listener(listener)
            ```
        """
        pass
