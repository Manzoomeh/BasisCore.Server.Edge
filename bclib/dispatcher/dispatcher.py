"""Base class for dispatching request"""
import asyncio
import inspect
import json
import re
import signal
import sys
import traceback
from functools import wraps
from struct import error
from typing import Any, Callable, Coroutine, Optional, Type

from bclib.cache import CacheFactory, CacheManager
from bclib.context import (ClientSourceContext, ClientSourceMemberContext,
                           Context, RabbitContext, RequestContext,
                           RESTfulContext, ServerSourceContext,
                           ServerSourceMemberContext, SocketContext,
                           WebContext, WebSocketContext)
from bclib.db_manager import DbManager
from bclib.dispatcher.dispatcher_helper import DispatcherHelper
from bclib.dispatcher.idispatcher import IDispatcher
from bclib.exception import HandlerNotFoundErr
from bclib.listener import (HttpBaseDataType, Message, MessageType,
                            RabbitBusListener, ReceiveMessage)
from bclib.listener.web_message import WebMessage
from bclib.listener.websocket_message import WebSocketMessage
from bclib.logger import ILogger, LoggerFactory, LogObject
from bclib.predicate import Predicate
from bclib.service_provider import InjectionPlan, ServiceProvider
from bclib.utility import DictEx
from bclib.utility.static_file_handler import StaticFileHandler
from bclib.websocket import WebSocketSessionManager

from ..dispatcher.callback_info import CallbackInfo


class Dispatcher(DispatcherHelper, IDispatcher):
    """
    Base class for dispatching requests with integrated dependency injection

    Provides a flexible routing system for different context types (RESTful, WebSocket, etc.)
    with automatic service resolution and handler registration capabilities.

    Features:
        - Automatic dependency injection for handlers
        - Multiple context type support (RESTful, Socket, WebSocket, RabbitMQ, etc.)
        - Service lifetime management (singleton, scoped, transient)
        - Dynamic handler registration/unregistration
        - Predicate-based routing
        - Background task support

    Example:
        ```python
        from bclib import edge

        # Create dispatcher
        app = edge.from_options({"server": "localhost:8080", "router": "restful"})

        # Register services
        app.add_singleton(ILogger, ConsoleLogger)
        app.add_scoped(IDatabase, PostgresDatabase)

        # Register handlers with DI
        @app.restful_action(app.url("api/users"))
        async def get_users(logger: ILogger, db: IDatabase):
            logger.log("Fetching users")
            return db.get_all_users()

        # Or register programmatically
        app.register_handler(RESTfulContext, get_users, [app.url("api/users")])

        # Start server
        app.listening()
        ```
    """

    def __init__(self, options: dict = None, loop: asyncio.AbstractEventLoop = None):
        self.__options = DictEx(options)
        self.__look_up: 'dict[Type, list[CallbackInfo]]' = dict()
        self.__service_provider = ServiceProvider()
        cache_options = self.__options.cache if "cache" in self.__options else None
        if loop is None and sys.platform == 'win32':
            # By default Windows can use only 64 sockets in asyncio loop. This is a limitation of underlying select() API call.
            # Use Windows version of proactor event loop using IOCP
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
        self.__event_loop = asyncio.get_event_loop() if loop is None else loop
        self.__cache_manager = CacheFactory.create(cache_options)
        self.__db_manager = DbManager(self.__options, self.__event_loop)
        self.__logger: ILogger = LoggerFactory.create(self.__options)
        self.__log_error: bool = self.__options.log_error if self.__options.has(
            "log_error") else False
        self.__log_request: bool = self.__options.log_request if self.__options.has(
            "log_request") else True

        # Routing configuration
        self.__default_router = self.__options.defaultRouter\
            if 'defaultRouter' in self.__options and isinstance(self.__options.defaultRouter, str)\
            else None
        self.name = self.__options["name"] if self.__options.has(
            "name") else None
        self.__log_name = f"{self.name}: " if self.name else ''
        self.__context_type_detector: Optional['Callable[[str],str]'] = None
        self.__manual_router_config = False  # Track if router was manually configured

        # Initialize WebSocket session manager
        self.__ws_manager = WebSocketSessionManager(
            on_message_receive_async=self.on_message_receive_async,
            heartbeat_interval=30.0
        )

        # Initialize listeners collection
        self.__listeners: list = []

        # Add Rabbit listeners if configured
        if "router" in self.__options and "rabbit" in self.__options.router:
            for setting in self.__options.router.rabbit:
                rabbit_listener = RabbitBusListener(setting, self)
                self.__listeners.append(rabbit_listener)

        # Configure router
        if self.__options.has('router'):
            self.__manual_router_config = True
            router = self.__options.router
            if isinstance(router, str):
                self.__context_type_detector: 'Callable[[str],str]' = lambda _: router
            elif isinstance(router, DictEx):
                self.__init_router_lookup()
            else:
                raise error(
                    "Invalid value for 'router' property in host options! Use string or dict object only.")
        elif self.__default_router:
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: self.__default_router

    # Properties for IDispatcher interface
    @property
    def options(self) -> DictEx:
        """Get dispatcher options"""
        return self.__options

    @property
    def event_loop(self) -> asyncio.AbstractEventLoop:
        """Get event loop"""
        return self.__event_loop

    @property
    def cache_manager(self) -> 'CacheManager':
        """Get cache manager"""
        return self.__cache_manager

    @property
    def db_manager(self) -> DbManager:
        """Get database manager"""
        return self.__db_manager

    @property
    def log_error(self) -> bool:
        """Get log error setting"""
        return self.__log_error

    @property
    def log_request(self) -> bool:
        """Get log request setting"""
        return self.__log_request

    def add_singleton(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable[['ServiceProvider'], Any]] = None,
        instance: Optional[Any] = None
    ) -> 'Dispatcher':
        """
        Register a singleton service (one instance for entire application lifetime)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives ServiceProvider
            instance: Pre-created instance

        Returns:
            Self for chaining

        Example:
            ```python
            dispatcher.add_singleton(ILogger, ConsoleLogger)
            dispatcher.add_singleton(IConfig, instance=config)
            dispatcher.add_singleton(IDatabase, factory=lambda sp: PostgresDB(sp.get_service(ILogger)))
            ```
        """
        self.__service_provider.add_singleton(
            service_type, implementation, factory, instance)
        return self

    def add_scoped(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable[['ServiceProvider'], Any]] = None
    ) -> 'Dispatcher':
        """
        Register a scoped service (one instance per request/scope)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives ServiceProvider

        Returns:
            Self for chaining

        Example:
            ```python
            dispatcher.add_scoped(IDatabase, PostgresDatabase)
            dispatcher.add_scoped(ICache, factory=lambda sp: RedisCache(sp.get_service(ILogger)))
            ```
        """
        self.__service_provider.add_scoped(
            service_type, implementation, factory)
        return self

    def add_transient(
        self,
        service_type: Type,
        implementation: Optional[Type] = None,
        factory: Optional[Callable[['ServiceProvider'], Any]] = None
    ) -> 'Dispatcher':
        """
        Register a transient service (new instance every time)

        Args:
            service_type: The service interface/type
            implementation: Concrete implementation class
            factory: Factory function that receives ServiceProvider

        Returns:
            Self for chaining

        Example:
            ```python
            dispatcher.add_transient(IEmailService, SmtpEmailService)
            dispatcher.add_transient(INotifier, factory=lambda sp: Notifier(sp.get_service(ILogger)))
            ```
        """
        self.__service_provider.add_transient(
            service_type, implementation, factory)
        return self

    def create_scope(self) -> ServiceProvider:
        """
        Create a new scope for scoped services (per-request)

        Returns:
            New ServiceProvider with same registrations but fresh scoped instances

        Example:
            ```python
            # Create scope for each request
            request_services = dispatcher.create_scope()

            # Use scoped services
            db = request_services.get_service(IDatabase)

            # Clean up after request
            request_services.clear_scope()
            ```
        """
        return self.__service_provider.create_scope()

    def get_service(self, service_type: Type, **kwargs) -> Any:
        """
        Get a service instance from the DI container

        Args:
            service_type: The service interface/type to resolve
            **kwargs: Additional parameters to pass to the service constructor

        Returns:
            Instance of the requested service

        Example:
            ```python
            logger = dispatcher.get_service(ILogger)
            db = dispatcher.get_service(IDatabase, connection_string="...")
            ```
        """
        return self.__service_provider.get_service(service_type, **kwargs)

    def register_handler(
        self,
        context_type: Type[Context],
        handler: Callable,
        predicates: list[Predicate] = None
    ) -> 'Dispatcher':
        """
        Register a handler for a specific context type without using decorators

        Args:
            context_type: The context type (RESTfulContext, SocketContext, etc.)
            handler: The handler function (can be sync or async)
            predicates: List of predicates for routing

        Returns:
            Self for chaining

        Example:
            ```python
            def my_handler(context: RESTfulContext, logger: ILogger):
                return {"message": "Hello"}

            dispatcher.register_handler(
                RESTfulContext,
                my_handler,
                [dispatcher.url("api/hello")]
            )
            ```
        """
        if predicates is None:
            predicates = []

        # Map context types to their decorator methods
        decorator_map = {
            SocketContext: self.socket_action,
            RESTfulContext: self.restful_action,
            WebContext: self.web_action,
            WebSocketContext: self.websocket_action,
            ClientSourceContext: self.client_source_action,
            ClientSourceMemberContext: self.client_source_member_action,
            ServerSourceContext: self.server_source_action,
            ServerSourceMemberContext: self.server_source_member_action,
            RabbitContext: self.rabbit_action,
        }

        # Get appropriate decorator
        decorator = decorator_map.get(context_type)
        if decorator is None:
            raise ValueError(f"Unsupported context type: {context_type}")

        # Apply decorator to handler
        decorator(*predicates)(handler)

        # Rebuild router if auto-generated
        self.__rebuild_router_if_needed()

        return self

    def unregister_handler(
        self,
        context_type: Type[Context],
        handler: Callable = None
    ) -> 'Dispatcher':
        """
        Unregister handler(s) for a specific context type

        Args:
            context_type: The context type (RESTfulContext, SocketContext, etc.)
            handler: Specific handler to remove. If None, removes all handlers for this context type

        Returns:
            Self for chaining

        Example:
            ```python
            # Remove specific handler
            dispatcher.unregister_handler(RESTfulContext, my_handler)

            # Remove all handlers for context type
            dispatcher.unregister_handler(RESTfulContext)
            ```
        """
        handlers = self._get_context_lookup(context_type)

        if handler is None:
            # Remove all handlers for this context type
            handlers.clear()
        else:
            # Remove specific handler by matching the original function
            # The wrapper contains __wrapped__ attribute pointing to original
            handlers[:] = [
                callback_info for callback_info in handlers
                if not (hasattr(callback_info._CallbackInfo__async_callback, '__wrapped__') and
                        callback_info._CallbackInfo__async_callback.__wrapped__ is handler)
            ]

        # Rebuild router if auto-generated
        self.__rebuild_router_if_needed()

        return self

    def socket_action(self, * predicates: (Predicate)):
        """
        Decorator for Socket action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: SocketContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: SocketContext, logger: ILogger)
        """

        def _decorator(socket_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(socket_action_handler)

            @wraps(socket_action_handler)
            async def wrapper(context: SocketContext):
                kwargs = context.url_segments if context.url_segments else {}
                await injection_plan.execute_async(self.__service_provider, self.event_loop, **kwargs)
                return True

            self._get_context_lookup(SocketContext)\
                .append(CallbackInfo([*predicates], wrapper))
            return socket_action_handler
        return _decorator

    def restful_action(self, * predicates: (Predicate)):
        """
        Decorator for RESTful action with automatic DI

        Context parameter is now optional - handler can choose to:
        - Accept context: def handler(context: RESTfulContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: RESTfulContext, logger: ILogger)
        """

        def _decorator(restful_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(restful_action_handler)

            @wraps(restful_action_handler)
            async def wrapper(context: RESTfulContext):
                # ✨ Execute pre-compiled plan (fast - no reflection)
                kwargs = context.url_segments if context.url_segments else {}
                action_result = await injection_plan.execute_async(
                    self.__service_provider, self.event_loop, **kwargs)
                return None if action_result is None else context.generate_response(action_result)

            self._get_context_lookup(RESTfulContext)\
                .append(CallbackInfo([*predicates], wrapper))
            return restful_action_handler
        return _decorator

    def web_action(self, * predicates: (Predicate)):
        """
        Decorator for legacy web request action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: WebContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: WebContext, logger: ILogger)
        """

        def _decorator(web_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(web_action_handler)

            @wraps(web_action_handler)
            async def wrapper(context: WebContext):
                kwargs = context.url_segments if context.url_segments else {}
                action_result = await injection_plan.execute_async(self.__service_provider, self.event_loop, **kwargs)
                return None if action_result is None else context.generate_response(action_result)

            self._get_context_lookup(WebContext)\
                .append(CallbackInfo([*predicates], wrapper))
            return web_action_handler
        return _decorator

    def websocket_action(self, * predicates: (Predicate)):
        """
        Decorator for WebSocket action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: WebSocketSession)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: WebSocketSession, logger: ILogger)
        """

        def _decorator(websocket_action_handler: Callable):
            from bclib.dispatcher.websocket_session import WebSocketSession

            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(websocket_action_handler)

            @wraps(websocket_action_handler)
            async def wrapper(context: WebSocketSession):
                kwargs = context.url_segments if context.url_segments else {}
                return await injection_plan.execute_async(self.__service_provider, self.event_loop, **kwargs)

            self._get_context_lookup(WebSocketContext)\
                .append(CallbackInfo([*predicates], wrapper))
            return websocket_action_handler
        return _decorator

    def client_source_action(self, *predicates: (Predicate)):
        """
        Decorator for client source action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: ClientSourceContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: ClientSourceContext, logger: ILogger)
        """

        def _decorator(client_source_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(client_source_action_handler)

            @wraps(client_source_action_handler)
            async def wrapper(context: ClientSourceContext):
                kwargs = context.url_segments if context.url_segments else {}
                data = await injection_plan.execute_async(self.__service_provider, self.event_loop, **kwargs)
                result_set = list()
                if data is not None:
                    for member in context.command.member:
                        member_context = ClientSourceMemberContext(
                            context, data, member)
                        dispatch_result = await self.dispatch_async(member_context)
                        result = {
                            "options": {
                                "tableName": member_context.table_name,
                                "keyFieldName": member_context.key_field_name,
                                "statusFieldName": member_context.status_field_name,
                                "mergeType": member_context.merge_type.value,
                                "columnNames": member_context.column_names,
                            },
                            "data": dispatch_result
                        }
                        result_set.append(result)
                    ret_val = {
                        "setting": {
                            "keepalive": False,
                        },
                        "sources": result_set
                    }
                    return context.generate_response(ret_val)
                else:
                    return None

            self._get_context_lookup(ClientSourceContext)\
                .append(CallbackInfo([*predicates], wrapper))

            return client_source_action_handler
        return _decorator

    def client_source_member_action(self, *predicates: (Predicate)):
        """
        Decorator for client source member action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: ClientSourceMemberContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: ClientSourceMemberContext, logger: ILogger)
        """

        def _decorator(client_source_member_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(client_source_member_handler)

            @wraps(client_source_member_handler)
            async def wrapper(context: ClientSourceMemberContext):
                kwargs = context.url_segments if context.url_segments else {}
                return await injection_plan.execute_async(self.__service_provider, self.event_loop, **kwargs)

            self._get_context_lookup(ClientSourceMemberContext)\
                .append(CallbackInfo([*predicates], wrapper))
            return client_source_member_handler
        return _decorator

    def server_source_action(self, *predicates: (Predicate)):
        """
        Decorator for server source action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: ServerSourceContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: ServerSourceContext, logger: ILogger)
        """

        def _decorator(server_source_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(server_source_action_handler)

            @wraps(server_source_action_handler)
            async def wrapper(context: ServerSourceContext):
                kwargs = context.url_segments if context.url_segments else {}
                data = await injection_plan.execute_async(self.__service_provider, self.event_loop, **kwargs)
                result_set = list()
                if data is not None:
                    for member in context.command.member:
                        member_context = ServerSourceMemberContext(
                            context, data, member)
                        dispatch_result = await self.dispatch_async(member_context)
                        result = {
                            "options": {
                                "tableName": member_context.table_name,
                                "keyFieldName": member_context.key_field_name,
                                "statusFieldName": member_context.status_field_name,
                                "mergeType": member_context.merge_type.value,
                                "columnNames": member_context.column_names,
                            },
                            "data": dispatch_result
                        }
                        result_set.append(result)
                    ret_val = {
                        "setting": {
                            "keepalive": False,
                        },
                        "sources": result_set
                    }
                    return context.generate_response(ret_val)
                else:
                    return None

            self._get_context_lookup(ServerSourceContext)\
                .append(CallbackInfo([*predicates], wrapper))

            return server_source_action_handler
        return _decorator

    def server_source_member_action(self, *predicates: (Predicate)):
        """
        Decorator for server source member action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: ServerSourceMemberContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: ServerSourceMemberContext, logger: ILogger)
        """

        def _decorator(server_source_member_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(server_source_member_action_handler)

            @wraps(server_source_member_action_handler)
            async def wrapper(context: ServerSourceMemberContext):
                kwargs = context.url_segments if context.url_segments else {}
                return await injection_plan.execute_async(self.__service_provider, self.event_loop, **kwargs)

            self._get_context_lookup(ServerSourceMemberContext)\
                .append(CallbackInfo([*predicates], wrapper))
            return server_source_member_action_handler
        return _decorator

    def rabbit_action(self, * predicates: (Predicate)):
        """
        Decorator for RabbitMQ message action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: RabbitContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: RabbitContext, logger: ILogger)
        """

        def _decorator(rabbit_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(rabbit_action_handler)

            @wraps(rabbit_action_handler)
            async def wrapper(context: RabbitContext):
                kwargs = context.url_segments if context.url_segments else {}
                return await injection_plan.execute_async(self.__service_provider, self.event_loop, **kwargs)

            self._get_context_lookup(RabbitContext)\
                .append(CallbackInfo([*predicates], wrapper))

            return rabbit_action_handler
        return _decorator

    def _get_context_lookup(self, key: Type) -> 'list[CallbackInfo]':
        """Get key related action list object"""

        ret_val: None
        if key in self.__look_up:
            ret_val = self.__look_up[key]
        else:
            ret_val = list()
            self.__look_up[key] = ret_val
        return ret_val

    async def dispatch_async(self, context: Context) -> Any:
        """Dispatch context and get result from related action method"""

        result: Any = None
        context_type = type(context)
        try:
            items = self._get_context_lookup(context_type)
            for item in items:
                result = await item.try_execute_async(context)
                if result is not None:
                    break
            else:
                ex = HandlerNotFoundErr(context_type.__name__)
                if self.log_error:
                    print(str(ex))
                result = context.generate_error_response(ex)
        except Exception as ex:
            if self.log_error:
                traceback.print_exc()
            result = context.generate_error_response(ex)
        return result

    def dispatch_in_background(self, context: 'Context') -> asyncio.Future:
        """Dispatch context in background"""

        return self.event_loop.create_task(self.dispatch_async(context))

    def __build_router_from_lookup(self):
        """Auto-generate router from registered handlers in lookup"""
        from bclib.predicate.url import Url

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
        context_patterns = {}

        for ctx_type, handlers in self.__look_up.items():
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
                        regex_pattern = re.sub(
                            r':(\w+)', r'(?P<\1>[^/]+)', pattern)
                        context_patterns[context_name].append(regex_pattern)

        available_contexts = list(context_patterns.keys())

        if len(available_contexts) == 0:
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: "socket"
            self.__default_router = "socket"
        elif len(available_contexts) == 1:
            default = available_contexts[0]
            self.__context_type_detector: 'Callable[[str],str]' = lambda _: default
            self.__default_router = default
        else:
            route_lookup = []
            for context_name, patterns in context_patterns.items():
                for pattern in patterns:
                    route_lookup.append((pattern, context_name))
            self.__context_type_lookup = route_lookup
            self.__context_type_detector = self.__context_type_detect_from_lookup
            self.__default_router = available_contexts[0]

    def __init_router_lookup(self):
        """Initialize router lookup dictionary from configuration"""
        route_dict = dict()
        for key, values in self.__options.router.items():
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
        """Ensure router is initialized before message processing"""
        if self.__context_type_detector is None:
            self.__build_router_from_lookup()

    def __rebuild_router_if_needed(self):
        """Rebuild router if auto-generated"""
        if not self.__manual_router_config:
            self.__build_router_from_lookup()

    def __context_type_detect_from_lookup(self, url: str) -> str:
        """Detect context type from URL using lookup patterns"""
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

    async def on_message_receive_async(self, message: Message) -> Message:
        """Process received message and dispatch to appropriate handler

        This is the main entry point for listeners to send messages to the dispatcher.
        """
        try:
            context = self.__context_factory(message)
            response = await self.dispatch_async(context)
            ret_val: Message = None
            if context.is_adhoc:
                ret_val = message.create_response_message(
                    message.session_id,
                    response
                )
            return ret_val
        except Exception as ex:
            print(f"Error in process received message {ex}")
            raise ex

    def __context_factory(self, message: Message) -> Context:
        """Create appropriate context type from message"""
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
            print(f"{self.__log_name}({context_type}::{message.type.name}){f' - {request_id} {method} {url} ' if cms_object else ''}")

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
        """Get WebSocket session manager"""
        return self.__ws_manager

    def run_in_background(self, callback: 'Callable|Coroutine', *args: Any) -> asyncio.Future:
        """Execute function or coroutine in background"""
        if inspect.iscoroutinefunction(callback):
            return self.event_loop.create_task(callback(*args))
        else:
            return self.event_loop.run_in_executor(None, callback, *args)

    def add_listener(self, listener: Any):
        """Add a listener to the dispatcher

        Args:
            listener: Listener instance (HttpListener, SocketListener, etc.)
        """
        self.__listeners.append(listener)

    async def send_message_async(self, message: Message) -> bool:
        """Send ad-hoc message to endpoint via SocketListener

        Args:
            message: Message to send

        Returns:
            Success status

        Raises:
            NotImplementedError: If no SocketListener is configured

        Note:
            This method requires a SocketListener to be added to the dispatcher.
            The SocketListener reference should be stored in _socket_listener attribute.
        """
        if hasattr(self, '_socket_listener'):
            # Use SocketListener's send method with lock
            if not hasattr(self, '_send_lock'):
                self._send_lock = asyncio.Lock()
            async with self._send_lock:
                return await self._socket_listener.send_message_async(message)
        else:
            raise NotImplementedError(
                "Send ad-hoc message requires SocketListener. Add SocketListener to dispatcher.")

    def initialize_task(self):
        """Initialize all listeners and tasks"""
        # Ensure router is ready before server starts
        self.__ensure_router_initialized()

        # Initialize all added listeners (HTTP, Socket, Rabbit, etc.)
        for listener in self.__listeners:
            listener.initialize_task(self.event_loop)

        # Initialize endpoint listener if configured
        if hasattr(self, '_endpoint_connection_handler') and hasattr(self, '_endpoint'):
            async def start_endpoint_server():
                server = await asyncio.start_server(
                    self._endpoint_connection_handler,
                    self._endpoint.host,
                    self._endpoint.port
                )
                async with server:
                    await server.serve_forever()

            self.event_loop.create_task(start_endpoint_server())

    def listening(self, before_start: Coroutine = None, after_end: Coroutine = None, with_block: bool = True):
        """Start listening to request for process"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda sig, _: self.event_loop.stop())
        if before_start != None:
            self.event_loop.run_until_complete(
                self.event_loop.create_task(before_start()))
        self.initialize_task()
        if with_block:
            self.event_loop.run_forever()
            tasks = asyncio.all_tasks(loop=self.event_loop)
            for task in tasks:
                task.cancel()
            group = asyncio.gather(*tasks, return_exceptions=True)
            self.event_loop.run_until_complete(group)
            if after_end != None:
                self.event_loop.run_until_complete(
                    self.event_loop.create_task(after_end()))
            self.event_loop.close()

    def new_object_log(self, schema_name: str, routing_key: Optional[str] = None, **kwargs) -> LogObject:
        return self.__logger.new_object_log(schema_name, routing_key, **kwargs)

    async def log_async(self, log_object: LogObject = None, **kwargs):
        """log params"""
        if log_object is None:
            if "schema_name" not in kwargs:
                raise Exception("'schema_name' not set for apply logging!")
            schema_name = kwargs.pop("schema_name")
            log_object = self.new_object_log(schema_name, **kwargs)
        await self.__logger.log_async(log_object)

    def log_in_background(self, log_object: LogObject = None, **kwargs) -> Coroutine:
        """log params in background precess"""
        return self.event_loop.create_task(
            self.log_async(log_object, **kwargs)
        )

    def add_static_handler(self, handler: StaticFileHandler) -> None:
        """Add static file handler to dispatcher"""
        async def async_wrapper(context: WebContext):
            action_result = await handler.handle(context)
            return None if action_result is None else context.generate_response(action_result)

        self._get_context_lookup(WebContext)\
            .append(CallbackInfo([], async_wrapper))

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
