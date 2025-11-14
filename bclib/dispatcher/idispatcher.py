"""Dispatcher base class module"""
import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional

from bclib.cache import CacheManager
from bclib.db_manager import DbManager
from bclib.listener import Message
from bclib.logger import LogObject
from bclib.utility import DictEx
from bclib.utility.service_provider import ServiceProvider

if TYPE_CHECKING:
    from context import Context


class IDispatcher(ABC):
    """Dispatcher base class with core functionality for manage cache and background process"""

    @property
    @abstractmethod
    def log_error(self) -> bool:
        pass

    @property
    @abstractmethod
    def log_request(self) -> bool:
        pass

    @property
    @abstractmethod
    def event_loop(self) -> asyncio.AbstractEventLoop:
        pass

    @property
    @abstractmethod
    def db_manager(self) -> DbManager:
        pass

    @property
    @abstractmethod
    def options(self) -> DictEx:
        pass

    @property
    @abstractmethod
    def cache_manager(self) -> CacheManager:
        pass

    @property
    @abstractmethod
    def services(self) -> ServiceProvider:
        """Get the service provider (DI container)"""
        pass

    @abstractmethod
    async def dispatch_async(self, context: 'Context') -> Any:
        """Dispatch context and get result from related action method"""

    @abstractmethod
    def dispatch_in_background(self, context: 'Context') -> asyncio.Future:
        """Dispatch context in background"""

    @abstractmethod
    async def send_message_async(self, message: Message) -> None:
        """Send message to endpoint"""

    def run_in_background(self, callback: Callable, *args: Any) -> asyncio.Future:
        """helper for run function in background thread"""

    def new_object_log(self, schema_name: str, routing_key: Optional[str] = None, **kwargs) -> LogObject:
        """Create new log object"""

    async def log_async(self, log_object: LogObject = None, **kwargs):
        """log params"""

    def log_in_background(self, log_object: LogObject = None, **kwargs) -> Coroutine:
        """log params in background precess"""
