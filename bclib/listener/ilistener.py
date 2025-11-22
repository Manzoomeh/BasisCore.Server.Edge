"""Base Listener Interface - abstract base class for all listeners"""
import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from bclib.listener import Message


class IListener(ABC):
    """
    Abstract base class for all listener implementations

    All listeners (HttpListener, EndpointListener, RabbitBusListener, etc.)
    must inherit from this class and implement the initialize_task method.

    The dispatcher calls initialize_task to start the listener's async tasks
    on the event loop.

    Example:
        ```python
        class MyCustomListener(IListener):
            def __init__(self, endpoint, on_message_receive_async):
                self.__endpoint = endpoint
                self.__on_message_receive = on_message_receive_async

            def initialize_task(self, event_loop: asyncio.AbstractEventLoop):
                event_loop.create_task(self.__server_task())

            async def __server_task(self):
                # Start server and handle connections
                pass
        ```
    """

    def __init__(
        self,
        on_message_receive_async: Callable[['Message'], Awaitable[None]]
    ):
        """
        Initialize base listener

        Args:
            on_message_receive_async: Async callback to process received messages
        """
        self._on_message_receive = on_message_receive_async

    @abstractmethod
    def initialize_task(self, event_loop: asyncio.AbstractEventLoop) -> None:
        """
        Initialize listener tasks on the event loop

        This method is called by the dispatcher during startup to initialize
        and start the listener's async tasks.

        Args:
            event_loop: asyncio event loop to run tasks on

        Example:
            ```python
            def initialize_task(self, event_loop: asyncio.AbstractEventLoop):
                # Create server task
                event_loop.create_task(self.__start_server_async())

                # Create background tasks if needed
                event_loop.create_task(self.__heartbeat_async())
            ```
        """
        pass
