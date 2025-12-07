"""Dispatcher base class module"""
import asyncio
from abc import ABC, abstractmethod
from collections.abc import Coroutine
from typing import TYPE_CHECKING, Any, Callable, Optional

from bclib.cache.manager import CacheManager
from bclib.options.app_options import AppOptions
from bclib.predicate.predicate import Predicate
from bclib.predicate.predicate_helper import PredicateHelper
from bclib.utility.static_file_handler import StaticFileHandler

if TYPE_CHECKING:

    from bclib.context.context import Context
    from bclib.service_provider.iservice_provider import IServiceProvider


class IDispatcher(PredicateHelper, ABC):
    """Dispatcher base class with core functionality for manage cache and background process"""

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
    def handler(self, route: Optional[str] = None, method: Optional[str | list[str]] = None, *predicates: Predicate):
        """
        Universal handler decorator that automatically determines the action type based on handler's context parameter

        This decorator inspects the handler's signature to find the context type parameter and automatically
        routes to the appropriate specific handler decorator (web_handler, restful_handler, websocket_handler, etc.).

        Example:
            ```python
            # Automatically uses restful_handler because context is RESTfulContext
            @app.handler("users/:id", method="GET")
            def get_user(context: RESTfulContext):
                return {"user_id": context.url_segments['id']}

            # Automatically uses web_handler because context is HttpContext
            @app.handler("home", method="GET")
            def home_page(context: HttpContext):
                return "<h1>Home Page</h1>"

            # Automatically uses websocket_handler because context is WebSocketContext
            @app.handler("ws/chat/:room")
            async def chat_handler(context: WebSocketContext):
                await context.send_text(f"Welcome to room {context.url_segments['room']}")

            # Works without context parameter too (inspects other type hints)
            @app.handler("api/data")
            def get_data():
                return {"data": "value"}
            ```

        Note:
            The decorator determines the action type by inspecting the handler's type hints.
            If no context type is found, it defaults to restful_handler.
        """
        pass
