import asyncio
import inspect
import json
import re
from struct import error
from typing import Any, Callable, Coroutine, Optional, Type

from bclib.context import (ClientSourceContext, Context, RequestContext,
                           RESTfulContext, ServerSourceContext, SocketContext,
                           WebContext, WebSocketContext)
from bclib.dispatcher.dispatcher import Dispatcher
from bclib.dispatcher.dispatcher_helper import DispatcherHelper
from bclib.dispatcher.websocket_session_manager import WebSocketSessionManager
from bclib.listener import (HttpBaseDataType, Message, MessageType,
                            ReceiveMessage)
from bclib.listener.web_message import WebMessage
from bclib.listener.websocket_message import WebSocketMessage
from bclib.predicate import Predicate
from bclib.service_provider import ServiceProvider
from bclib.utility import DictEx


class RoutingDispatcher(Dispatcher, DispatcherHelper):
    """
    Dispatcher with URL-based routing and message processing capabilities

    Extends base Dispatcher with automatic context type detection based on registered handlers.
    Router configuration is now optional - if not provided, it will be auto-generated from
    registered handlers in the lookup.

    Features:
        - URL pattern-based routing (regex support)
        - Automatic context type detection
        - Auto-generated router from handler registration
        - WebSocket session management
        - Multiple message protocol support
        - Configurable default router
        - Background task execution

    Routing Configuration (Optional):
        ```python
        # Manual configuration (legacy)
        options = {
            "router": {
                "restful": ["api/*", "v1/*"],
                "websocket": ["ws/*"],
                "web": ["*"]  # Catch-all
            },
            "defaultRouter": "restful"
        }

        dispatcher = RoutingDispatcher(options)
        ```

    Example:
        ```python
        from bclib.dispatcher import RoutingDispatcher

        # Simple: router auto-generated from handlers
        options = {
            "server": "localhost:8080",
            "log_request": True
        }

        app = RoutingDispatcher(options)

        # Register handlers - router is built automatically
        @app.restful_action(app.url("api/users"))
        async def get_users():
            return {"users": []}

        @app.websocket_action()
        async def handle_ws(context):
            return {"message": "connected"}

        # Router is auto-generated: {RESTfulContext: "restful", WebSocketContext: "websocket"}

        app.listening()
        ```

    Note:
        If router is not specified in options, it will be automatically generated from
        registered handlers when listening() is called.
    """

    def __init__(self, options: dict, loop: asyncio.AbstractEventLoop = None):
        super().__init__(options=options, loop=loop)
        self.__default_router = self.options.defaultRouter\
            if 'defaultRouter' in self.options and isinstance(self.options.defaultRouter, str)\
            else None
        self.name = self.options["name"] if self.options.has("name") else None
        self.__log_name = f"{self.name}: " if self.name else ''
        self.__context_type_detector: Optional['Callable[[str],str]'] = None
        self.__manual_router_config = False  # Track if router was manually configured

        # Initialize WebSocket session manager
        self.__ws_manager = WebSocketSessionManager(
            on_message_receive_async=self._on_message_receive_async,
            heartbeat_interval=30.0
        )

        if self.options.has('router'):
            self.__manual_router_config = True
            router = self.options.router
            if isinstance(router, str):
                self.__context_type_detector: 'Callable[[str],str]' = lambda _: router
            elif isinstance(router, DictEx):
                self.init_router_lookup()
            else:
                raise error(
                    "Invalid value for 'router' property in host options! Use string or dict object only.")
        elif self.__default_router:
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: self.__default_router
        # If no router config, it will be auto-generated from lookup when needed

    def __build_router_from_lookup(self):
        """Auto-generate router from registered handlers in lookup

        Creates context type detector based on handlers registered via decorators.
        Analyzes URL patterns from predicates to build intelligent routing.

        Context Type Mapping:
            RESTfulContext -> "restful"
            WebContext -> "web"
            SocketContext -> "socket"
            WebSocketContext -> "websocket"
            ClientSourceContext -> "client_source"
            ServerSourceContext -> "server_source"

        Strategy:
            1. Group handlers by context type
            2. Extract URL patterns from predicates
            3. Build pattern-based routing rules
            4. RESTful gets api/* patterns, Web gets other patterns
        """
        from bclib.dispatcher.dispatcher import Dispatcher
        from bclib.predicate.url import Url

        # Access parent's lookup via protected method
        lookup = self._Dispatcher__look_up

        # Map context types to router names
        context_to_router = {
            RESTfulContext: "restful",
            WebContext: "web",
            SocketContext: "socket",
            WebSocketContext: "websocket",
            ClientSourceContext: "client_source",
            ServerSourceContext: "server_source"
        }

        # Collect all URL patterns per context type
        context_patterns = {}  # {context_name: [patterns]}

        for ctx_type, handlers in lookup.items():
            if ctx_type not in context_to_router or len(handlers) == 0:
                continue

            context_name = context_to_router[ctx_type]
            context_patterns[context_name] = []

            # Extract URL patterns from predicates
            for callback_info in handlers:
                predicates = callback_info._CallbackInfo__predicates
                for predicate in predicates:
                    if isinstance(predicate, Url):
                        pattern = predicate.exprossion
                        # Convert BasisCore pattern to regex
                        # :param -> (?P<param>[^/]+)
                        regex_pattern = re.sub(
                            r':(\w+)', r'(?P<\1>[^/]+)', pattern)
                        context_patterns[context_name].append(regex_pattern)

        available_contexts = list(context_patterns.keys())

        if len(available_contexts) == 0:
            # No handlers registered, use socket as fallback
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: "socket"
            self.__default_router = "socket"
        elif len(available_contexts) == 1:
            # Single context type - use it for all
            default = available_contexts[0]
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: default
            self.__default_router = default
        else:
            # Multiple context types - create pattern-based routing
            # Build lookup: [(pattern, context_name), ...]
            route_lookup = []
            for context_name, patterns in context_patterns.items():
                for pattern in patterns:
                    route_lookup.append((pattern, context_name))

            self.__context_type_lookup = route_lookup
            self.__context_type_detector = self.__context_type_detect_from_lookup
            # Use first as default fallback
            self.__default_router = available_contexts[0]

    def init_router_lookup(self):
        """Initialize router lookup dictionary from configuration

        Creates a mapping of URL patterns to context types based on the router configuration.
        Supports wildcard patterns and regex for flexible routing.

        Router Configuration Format:
            {
                "restful": ["api/*", "v1/*"],
                "websocket": ["ws/*"],
                "web": ["*"]  # Catch-all pattern
            }

        Note:
            - Patterns are evaluated in order
            - "*" acts as a catch-all pattern
            - Regex patterns are supported
            - First match wins
        """

        route_dict = dict()
        for key, values in self.options.router.items():
            if key != 'rabbit'.strip():
                if '*' in values:
                    route_dict['*'] = key
                    break
                else:
                    for value in values:
                        if len(value.strip()) != 0 and value not in route_dict:
                            route_dict[value] = key
        if len(route_dict) == 1 and '*' in route_dict and self.__default_router is None:
            router = route_dict['*']
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: router
        else:
            self.__context_type_lookup = route_dict.items()
            self.__context_type_detector = self.__context_type_detect_from_lookup

    def __ensure_router_initialized(self):
        """Ensure router is initialized before message processing

        Auto-generates router from lookup if not configured manually.
        Called lazily on first message to allow all handlers to register first.
        """
        if self.__context_type_detector is None:
            self.__build_router_from_lookup()

    def __rebuild_router_if_needed(self):
        """
        Rebuild router if it was auto-generated (not manually configured)

        Called after dynamic handler registration/unregistration to keep
        router synchronized with current handler state.
        """
        # Only rebuild if router was auto-generated (not manual config)
        if not self.__manual_router_config:
            # Immediately rebuild to reflect changes
            self.__build_router_from_lookup()

    def register_handler(
        self,
        context_type: Type[Context],
        handler: Callable,
        predicates: list[Predicate] = None
    ) -> 'RoutingDispatcher':
        """
        Register a handler and rebuild router if needed

        Calls base class register_handler, then rebuilds router for auto-generated configs.

        Args:
            context_type: The context type (RESTfulContext, SocketContext, etc.)
            handler: The handler function (can be sync or async)
            predicates: List of predicates for routing

        Returns:
            Self for chaining

        Example:
            ```python
            app.register_handler(RESTfulContext, my_handler, [app.url("api/hello")])
            # Router automatically rebuilt if auto-generated
            ```
        """
        # Call base class to register handler
        super().register_handler(context_type, handler, predicates)

        # Rebuild router if auto-generated
        self.__rebuild_router_if_needed()

        return self

    def unregister_handler(
        self,
        context_type: Type[Context],
        handler: Callable = None
    ) -> 'RoutingDispatcher':
        """
        Unregister handler(s) and rebuild router if needed

        Calls base class unregister_handler, then rebuilds router for auto-generated configs.

        Args:
            context_type: The context type (RESTfulContext, SocketContext, etc.)
            handler: Specific handler to remove. If None, removes all handlers for this context type

        Returns:
            Self for chaining

        Example:
            ```python
            app.unregister_handler(RESTfulContext, my_handler)
            # Router automatically rebuilt if auto-generated
            ```
        """
        # Call base class to unregister handler
        super().unregister_handler(context_type, handler)

        # Rebuild router if auto-generated
        self.__rebuild_router_if_needed()

        return self

    def __context_type_detect_from_lookup(self, url: str) -> str:
        """Detect context type from URL using lookup patterns

        Args:
            url: The URL to match against patterns

        Returns:
            Context type string ("restful", "websocket", etc.) or default router

        Note:
            Uses regex matching for pattern evaluation
        """

        context_type: str = None
        if url:
            try:
                for pattern, lookup_context_type in self.__context_type_lookup:
                    if pattern == "*" or re.search(pattern, url):
                        context_type = lookup_context_type
                        break
            except TypeError:
                pass
            except error as ex:
                print("Error in detect context from routing options!", ex)
        return context_type if context_type else self.__default_router

    async def _on_message_receive_async(self, message: Message) -> Message:
        """Process received message and dispatch to appropriate handler

        Args:
            message: Incoming message from listener

        Returns:
            Response message for ad-hoc requests, None otherwise

        Workflow:
            1. Create context from message
            2. Dispatch to handler
            3. Generate response for ad-hoc requests

        Note:
            Router is already initialized in initialize_task() before server starts,
            so no need to check here.

        Raises:
            Exception: Re-raises any exception after logging
        """

        try:
            context = self.__context_factory(message)
            response = await self.dispatch_async(context)
            ret_val: Message = None
            if context.is_adhoc:
                # Pass raw response object; message implementation will handle serialization
                ret_val = message.create_response_message(
                    message.session_id,
                    response
                )
            return ret_val
        except Exception as ex:
            print(f"Error in process received message {ex}")
            raise ex

    def __context_factory(self, message: Message) -> Context:
        """Create appropriate context type from message

        Args:
            message: Message object (WebMessage, WebSocketMessage, etc.)

        Returns:
            Context instance (RESTfulContext, SocketContext, WebSocketContext, etc.)

        Raises:
            KeyError: If required keys missing in message
            NameError: If context type not found or unsupported

        Context Type Detection:
            - WebSocketMessage → WebSocketContext
            - AD_HOC message → URL-based routing
            - Other messages → SocketContext
        """

        ret_val: RequestContext = None
        context_type = None
        cms_object: Optional[dict] = None
        url: Optional[str] = None
        request_id: Optional[str] = None
        method: Optional[str] = None
        message_json: Optional[dict] = None
        if isinstance(message, WebMessage):
            message_json = message.cms_object
            cms_object = message_json.get(
                HttpBaseDataType.CMS) if message_json else None
        elif isinstance(message, WebSocketMessage):
            context_type = "websocket"
            cms_object = message.session.cms
        elif message.buffer is not None:
            message_json = json.loads(message.buffer)
            cms_object = message_json.get(
                HttpBaseDataType.CMS) if message_json else None
        if cms_object:
            if 'request' in cms_object:
                req = cms_object["request"]
            else:
                raise KeyError("request key not found in cms object")
            if 'full-url' in req:
                url = req["full-url"]
            else:
                raise KeyError("full-url key not found in request")
            request_id = req['request-id'] if 'request-id' in req else 'none'
            method = req['methode'] if 'methode' in req else 'none'
        if message.type == MessageType.AD_HOC:
            if url or self.__default_router is None:
                context_type = self.__context_type_detector(url)
            else:
                context_type = self.__default_router
        elif context_type is None:
            context_type = "socket"
        if self.log_request:
            print(
                f"{self.__log_name}({context_type}::{message.type.name}){f' - {request_id} {method} {url} ' if cms_object else ''}")

        if context_type == "client_source":
            ret_val = ClientSourceContext(cms_object, self, message)
        elif context_type == "restful":
            ret_val = RESTfulContext(cms_object, self, message)
        elif context_type == "server_source":
            ret_val = ServerSourceContext(message_json, self)
        elif context_type == "web":
            ret_val = WebContext(cms_object, self, message)
        elif context_type == "socket":
            ret_val = SocketContext(cms_object, self, message, message_json)
        elif context_type == "websocket":
            ret_val = WebSocketContext(cms_object, self, message)
        elif context_type is None:
            raise NameError(f"No context found for '{url}'")
        else:
            raise NameError(
                f"Configured context type '{context_type}' not found for '{url}'")
        return ret_val

    @property
    def ws_manager(self) -> WebSocketSessionManager:
        """Get WebSocket session manager

        Returns:
            WebSocketSessionManager instance for managing WebSocket connections

        Usage:
            ```python
            # Get active sessions
            sessions = dispatcher.ws_manager.sessions

            # Send message to session
            await dispatcher.ws_manager.send_to_session(session_id, message)
            ```
        """
        return self.__ws_manager

    def run_in_background(self, callback: 'Callable|Coroutine', *args: Any) -> asyncio.Future:
        """Execute function or coroutine in background

        Args:
            callback: Function or coroutine to execute
            *args: Arguments to pass to callback

        Returns:
            asyncio.Future representing the background task

        Example:
            ```python
            # Background task
            def long_task(data):
                # Process data
                return result

            future = dispatcher.run_in_background(long_task, my_data)

            # Async background task
            async def async_task(data):
                await process(data)

            future = dispatcher.run_in_background(async_task, my_data)
            ```
        """

        if inspect.iscoroutinefunction(callback):
            return self.event_loop.create_task(callback(*args))
        else:
            return self.event_loop.run_in_executor(None, callback, *args)

    def initialize_task(self):
        """Initialize tasks before server starts

        Overrides base class method to ensure router is initialized
        before any requests are processed. This is called by listening()
        before the event loop starts.

        Workflow:
            1. Initialize router from registered handlers (if auto-generated)
            2. Call parent's initialize_task for RabbitMQ setup
        """
        # Ensure router is ready before server starts
        self.__ensure_router_initialized()

        # Call parent to initialize RabbitMQ and other tasks
        super().initialize_task()

    async def send_message_async(self, message: MessageType) -> bool:
        """Send ad-hoc message to endpoint

        Args:
            message: Message to send

        Returns:
            Success status

        Raises:
            NotImplementedError: This dispatcher type does not support ad-hoc message sending

        Note:
            Override this method in subclasses to enable ad-hoc messaging
        """
        raise NotImplementedError(
            "Send ad-hoc message not support in this type of dispatcher")

    def cache(self, life_time: "int" = 0, key: "str" = None):
        """Decorator to cache function results

        Args:
            life_time: Cache duration in seconds (0 = cache forever until cleared)
            key: Optional cache key (for manual cache clearing)

        Returns:
            Decorator function

        Example:
            ```python
            # Time-based cache (60 seconds)
            @app.cache(life_time=60)
            async def get_data():
                return expensive_operation()

            # Key-based cache (clear manually)
            @app.cache(key="user_data")
            async def get_users():
                return db.query_users()

            # Clear cache by key
            app.cache_manager.clear("user_data")
            ```
        """

        return self.cache_manager.cache_decorator(key, life_time)
