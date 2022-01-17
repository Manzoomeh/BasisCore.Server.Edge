"""Dispatcher base class module"""
from abc import ABC, abstractmethod
from typing import Callable, Any, TYPE_CHECKING

from bclib.db_manager import DbManager
from bclib.cache import CacheManager
from bclib.listener import Message
from bclib.utility import DictEx

if TYPE_CHECKING:
    from context import Context


class IDispatcher(ABC):
    """Dispatcher base class with core functionality for manage cache and background process"""

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

    @abstractmethod
    def dispatch(self, context: 'Context') -> Any:
        """Dispatch context and get result from related action methode"""

    @abstractmethod
    def send_message(self, message: Message) -> None:
        """Send message to endpoint"""

    def run_in_background(self, callback: Callable, *args: Any) -> Any:
        """helper for run function in background thread"""
