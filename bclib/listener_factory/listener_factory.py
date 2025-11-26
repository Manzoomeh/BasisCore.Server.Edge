"""Listener Factory Implementation"""
from typing import TYPE_CHECKING

from bclib.app_options import AppOptions
from bclib.listener import (Endpoint, HttpListener, RabbitBusListener,
                            SocketListener)
from bclib.listener_factory.ilistener_factory import IListenerFactory
from bclib.utility import DictEx

if TYPE_CHECKING:
    from bclib.dispatcher import IDispatcher
    from bclib.listener import IListener


class ListenerFactory(IListenerFactory):
    """
    Factory for creating listeners based on application configuration

    Analyzes AppOptions and creates appropriate listeners:
    - HTTP/HTTPS listener (if 'server' option exists)
    - TCP Socket listener (if 'endpoint' option exists)
    - RabbitMQ listeners (if 'router.rabbit' option exists)

    Example:
        ```python
        options = {
            "server": "localhost:8080",
            "endpoint": "localhost:3000",
            "router": {
                "rabbit": [
                    {"host": "localhost", "queue": "tasks"}
                ]
            }
        }

        factory = ListenerFactory(options)
        listeners = factory.load_listeners(dispatcher)
        # Returns: [HttpListener, SocketListener, RabbitBusListener]
        ```
    """

    def __init__(self, options: AppOptions):
        """
        Initialize listener factory

        Args:
            options: Application configuration (AppOptions type alias for dict)
        """
        self.__options = options

    def load_listeners(self, dispatcher: 'IDispatcher') -> 'list[IListener]':
        """
        Create and return list of listeners based on configuration

        Examines the options dictionary for listener configurations and creates
        appropriate listener instances:

        - 'server' key → HttpListener (HTTP/HTTPS with optional SSL)
        - 'endpoint' key → SocketListener (TCP socket)
        - 'router.rabbit' key → RabbitBusListener (one per queue config)

        Args:
            dispatcher: Dispatcher instance for message handling

        Returns:
            list[IListener]: List of configured listener instances

        Example:
            ```python
            factory = ListenerFactory(options)
            listeners = factory.load_listeners(dispatcher)

            for listener in listeners:
                listener.initialize_task(event_loop)
            ```
        """
        listeners: list[IListener] = []

        # Add HTTP/HTTPS listener if server endpoint configured
        if "server" in self.__options:
            listener = HttpListener(
                Endpoint(self.__options.get('server')),
                dispatcher.on_message_receive_async,
                self.__options.get('ssl'),
                self.__options.get('configuration'),
                dispatcher.ws_manager
            )
            listeners.append(listener)

        # Add TCP endpoint listener if endpoint configured
        if "endpoint" in self.__options:
            listener = SocketListener(
                Endpoint(self.__options.get('endpoint')),
                dispatcher.on_message_receive_async
            )
            listeners.append(listener)

        # Add RabbitMQ listeners if configured
        if "router" in self.__options and "rabbit" in self.__options["router"]:
            for setting in self.__options["router"]["rabbit"]:
                listener = RabbitBusListener(
                    DictEx(setting), dispatcher)
                listeners.append(listener)

        return listeners
