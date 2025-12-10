"""Listener Factory Implementation"""
import asyncio
from typing import TYPE_CHECKING

from bclib.options.app_options import AppOptions
from bclib.service_provider.iservice_provider import IServiceProvider

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

    def __init__(self, service_provider: IServiceProvider,  options: AppOptions):
        """
        Initialize listener factory

        Args:
            options: Application configuration (AppOptions type alias for dict)
            loop: Event loop for async operations
            message_handler: Message handler instance for processing messages
        """
        self.__options = options
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

        # Add HTTP/HTTPS listener(s) if http configured
        if "http" in self.__options:
            http_config = self.__options.get('http')

            # Normalize to list - only handle array vs single item
            if isinstance(http_config, list):
                http_configs = http_config
            else:
                # Single item (string or dict)
                http_configs = [http_config]

            # Create listener for each config
            for config in http_configs:
                listener = self.__service_provider.create_instance(
                    HttpListener,
                    options=config
                )
                listeners.append(listener)

        # Add TCP listener(s) if tcp configured
        if "tcp" in self.__options:
            tcp_config = self.__options.get('tcp')

            # Normalize to list - only handle array vs single item
            if isinstance(tcp_config, list):
                tcp_configs = tcp_config
            else:
                # Single item (string or dict)
                tcp_configs = [tcp_config]

            # Create listener for each config
            for config in tcp_configs:
                listener = self.__service_provider.create_instance(
                    TcpListener,
                    options=config
                )
                listeners.append(listener)

        # Add RabbitMQ listener(s) if configured
        if "rabbit" in self.__options:
            rabbit_config = self.__options.get('rabbit')

            # Normalize to list - only handle array vs single item
            if isinstance(rabbit_config, list):
                rabbit_configs = rabbit_config
            else:
                # Single dict config
                rabbit_configs = [rabbit_config]

            # Create listener for each config
            for config in rabbit_configs:
                listener = self.__service_provider.create_instance(
                    RabbitListener,
                    options=config
                )
                listeners.append(listener)

        return listeners
