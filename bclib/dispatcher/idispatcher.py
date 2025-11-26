"""Dispatcher base class module"""
import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

from bclib.cache import CacheManager
from bclib.service_provider.iservice_provider import IServiceProvider

if TYPE_CHECKING:
    from context import Context


class IDispatcher(ABC):
    """Dispatcher base class with core functionality for manage cache and background process"""

    @property
    @abstractmethod
    def options(self) -> dict:
        pass

    @property
    @abstractmethod
    def cache_manager(self) -> CacheManager:
        pass

    @abstractmethod
    def create_scope(self) -> IServiceProvider:
        """Create a new scope for scoped services (per-request)"""
        pass

    @abstractmethod
    async def dispatch_async(self, context: 'Context') -> Any:
        """Dispatch context and get result from related action method"""

    @abstractmethod
    def dispatch_in_background(self, context: 'Context') -> asyncio.Future:
        """Dispatch context in background"""

    def run_in_background(self, callback: Callable, *args: Any) -> asyncio.Future:
        """helper for run function in background thread"""
