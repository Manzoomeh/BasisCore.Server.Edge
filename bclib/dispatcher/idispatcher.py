"""Dispatcher base class module"""
import asyncio
from abc import ABC, abstractmethod
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, Callable

from bclib.app_options import AppOptions
from bclib.cache.manager import CacheManager
from bclib.log_service.ilog_service import ILogService
from bclib.predicate.predicate_helper import PredicateHelper
from bclib.utility.static_file_handler import StaticFileHandler

if TYPE_CHECKING:
    from bclib.context.context import Context
    from bclib.listener.message import Message
    from bclib.service_provider.iservice_provider import IServiceProvider


class IDispatcher(PredicateHelper, ABC):
    """Dispatcher base class with core functionality for manage cache and background process"""

    @property
    @abstractmethod
    def Logger(self) -> ILogService:
        """Get logger service"""
        pass

    @property
    @abstractmethod
    def options(self) -> AppOptions:
        pass

    @property
    @abstractmethod
    def cache_manager(self) -> CacheManager:
        pass

    @property
    @abstractmethod
    def service_provider(self) -> 'IServiceProvider':
        """Get the root service provider (DI container)"""
        pass

    @abstractmethod
    async def dispatch_async(self, context: 'Context') -> Any:
        """Dispatch context and get result from related action method"""

    @abstractmethod
    def dispatch_in_background(self, context: 'Context') -> asyncio.Future:
        """Dispatch context in background"""
        pass

    @abstractmethod
    def run_in_background(self, callback: Callable, *args: Any) -> asyncio.Future:
        """helper for run function in background thread"""
        pass

    @abstractmethod
    def listening(self, before_start: Coroutine = None, after_end: Coroutine = None, with_block: bool = True):
        """Start listening to request for process"""
        pass

    @abstractmethod
    def add_static_handler(self, handler: StaticFileHandler) -> None:
        """Add static file handler to dispatcher"""
        pass

    @abstractmethod
    async def on_message_receive_async(self, message: 'Message') -> None:
        """Process received message and dispatch to appropriate handler

        This is the main entry point for listeners to send messages to the dispatcher.
        The method processes the message, dispatches it to the appropriate handler,
        and sets the response on the message object if it implements IResponseBaseMessage.

        Args:
            message: The message to process

        Note:
            This method does not return anything. For messages that implement
            IResponseBaseMessage, the response is set directly on the message object
            via message.set_response_async().
        """
        pass
