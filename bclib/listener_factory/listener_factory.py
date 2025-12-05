"""Listener Factory Implementation"""
import asyncio
from typing import TYPE_CHECKING

from bclib.app_options import AppOptions
from bclib.listener import Endpoint, HttpListener, TcpListener
from bclib.listener.rabbit.rabbit_listener import RabbitListener
from bclib.listener_factory.ilistener_factory import IListenerFactory
from bclib.utility import DictEx

if TYPE_CHECKING:
    from bclib.dispatcher import IDispatcher
    from bclib.listener import IListener


class ListenerFactory(IListenerFactory):
    """
    Factory for creating listeners based on application configuration

    Analyzes AppOptions and creates appropriate listeners:
    - HTTP/HTTPS listener (if 'http' option exists)
    - TCP listener (if 'tcp' option exists)
    - RabbitMQ listeners (if 'router.rabbit' option exists)

    Example:
        ```python
        options = {
            "http": "localhost:8080",
            "tcp": "localhost:3000",
            "router": {
                "rabbit": [
                    {"host": "localhost", "queue": "tasks"}
                ]
            }
        }

        factory = ListenerFactory(options)
        listeners = factory.load_listeners(dispatcher)
        # Returns: [HttpListener, TcpListener, RabbitBusListener]
        ```
    """

    def __init__(self, options: AppOptions, loop: asyncio.AbstractEventLoop):
        """
        Initialize listener factory

        Args:
            options: Application configuration (AppOptions type alias for dict)
        """
        self.__options = options
        self.__loop = loop

    def load_listeners(self, dispatcher: 'IDispatcher') -> 'list[IListener]':
        """
        Create and return list of listeners based on configuration

        Examines the options dictionary for listener configurations and creates
        appropriate listener instances:

        - 'http' key → HttpListener (HTTP/HTTPS with optional SSL)
        - 'tcp' key → TcpListener (TCP socket)
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

        # Add HTTP/HTTPS listener if http configured
        if "http" in self.__options:
            listener = dispatcher.service_provider.create_instance(HttpListener,
                                                                   endpoint=Endpoint(
                                                                       self.__options.get('http')),
                                                                   async_callback=dispatcher.on_message_receive_async,
                                                                   ssl_options=self.__options.get(
                                                                       'ssl'),
                                                                   configuration=self.__options.get(
                                                                       'configuration'),
                                                                   ws_manager=dispatcher.ws_manager
                                                                   )
            listeners.append(listener)

        # Add TCP listener if tcp configured
        if "tcp" in self.__options:
            listener = dispatcher.service_provider.create_instance(
                TcpListener,
                endpoint=Endpoint(self.__options.get('tcp')),
                on_message_receive_async=dispatcher.on_message_receive_async
            )
            listeners.append(listener)

        # Add RabbitMQ listeners if configured
        if "rabbit" in self.__options:
            listener = dispatcher.service_provider.create_instance(
                RabbitListener,
                connection_options=self.__options.get("rabbit"),
                async_callback=dispatcher.on_message_receive_async,
                loop=self.__loop
            )
            listeners.append(listener)

        return listeners
