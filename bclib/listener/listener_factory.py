"""Listener Factory Implementation"""
import asyncio
from typing import TYPE_CHECKING

from bclib.app_options import AppOptions
from bclib.dispatcher.imessage_handler import IMessageHandler
from bclib.service_provider.iservice_provider import IServiceProvider

from .endpoint import Endpoint
from .http.http_listener import HttpListener
from .ilistener_factory import IListenerFactory
from .rabbit.rabbit_listener import RabbitListener
from .tcp.tcp_listener import TcpListener

if TYPE_CHECKING:
    from .ilistener import IListener


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

        factory = ListenerFactory(options, loop, message_handler)
        listeners = factory.load_listeners()
        # Returns: [HttpListener, TcpListener, RabbitBusListener]
        ```
    """

    def __init__(self, service_provider: IServiceProvider,  options: AppOptions, loop: asyncio.AbstractEventLoop, message_handler: IMessageHandler):
        """
        Initialize listener factory

        Args:
            options: Application configuration (AppOptions type alias for dict)
            loop: Event loop for async operations
            message_handler: Message handler instance for processing messages
        """
        self.__options = options
        self.__loop = loop
        self.__message_handler = message_handler
        self.__service_provider = service_provider

    def load_listeners(self) -> 'list[IListener]':
        """
        Create and return list of listeners based on configuration

        Examines the options dictionary for listener configurations and creates
        appropriate listener instances:

        - 'http' key → HttpListener (HTTP/HTTPS with optional SSL)
        - 'tcp' key → TcpListener (TCP socket)
        - 'router.rabbit' key → RabbitBusListener (one per queue config)

        Returns:
            list[IListener]: List of configured listener instances

        Example:
            ```python
            factory = ListenerFactory(options, loop, message_handler)
            listeners = factory.load_listeners()

            for listener in listeners:
                listener.initialize_task(event_loop)
            ```
        """
        listeners: list[IListener] = []

        # Add HTTP/HTTPS listener if http configured
        if "http" in self.__options:
            listener = self.__service_provider.create_instance(HttpListener,
                                                               endpoint=Endpoint(
                                                                   self.__options.get('http')),
                                                               ssl_options=self.__options.get(
                                                                   'ssl'),
                                                               configuration=self.__options.get(
                                                                   'configuration')
                                                               )
            listeners.append(listener)

        # Add TCP listener if tcp configured
        if "tcp" in self.__options:
            listener = self.__service_provider.create_instance(
                TcpListener,
                endpoint=Endpoint(self.__options.get('tcp')),
            )
            listeners.append(listener)

        # Add RabbitMQ listeners if configured
        if "rabbit" in self.__options:
            listener = self.__service_provider.create_instance(
                RabbitListener,
                connection_options=self.__options.get("rabbit")
            )
            listeners.append(listener)

        return listeners
