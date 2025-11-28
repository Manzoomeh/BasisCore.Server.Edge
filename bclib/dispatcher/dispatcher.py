"""Base class for dispatching request"""
import asyncio
import inspect
import signal
import traceback
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Optional, Type

from bclib.app_options import AppOptions
from bclib.cache import CacheFactory, CacheManager
from bclib.context.context import Context
from bclib.dispatcher.callback_info import CallbackInfo
from bclib.dispatcher.context_factory import ContextFactory
from bclib.dispatcher.idispatcher import IDispatcher
from bclib.exception import HandlerNotFoundErr
from bclib.listener import IListener, Message
from bclib.listener.iresponse_base_message import IResponseBaseMessage
from bclib.listener_factory import IListenerFactory
from bclib.log_service.ilog_service import ILogService
from bclib.predicate import Predicate
from bclib.service_provider import InjectionPlan, IServiceProvider
from bclib.service_provider.iservice_provider import IServiceProvider
from bclib.utility.static_file_handler import StaticFileHandler
from bclib.websocket import WebSocketSessionManager


class Dispatcher(IDispatcher):
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
        async def get_users(options: AppOptions, logger: ILogger, db: IDatabase):
            logger.log(f"Fetching users from {options.get('name')}")
            return db.get_all_users()

        # Or register programmatically
        app.register_handler(RESTfulContext, get_users, [app.url("api/users")])

        # Start server
        app.listening()
        ```
    """

    def __init__(self, service_provider: IServiceProvider, options: AppOptions, logger: ILogService, loop: asyncio.AbstractEventLoop, listener_factory: IListenerFactory):
        """Initialize dispatcher with injected dependencies

        Args:
            service_provider: The DI container with all registered services
            options: Application configuration (AppOptions type alias for dict)
            loop: The asyncio event loop for async operations
            listener_factory: Factory for creating listeners based on configuration
        """
        self.__options = options
        self.__look_up: 'dict[Type, list[CallbackInfo]]' = dict()
        self.__service_provider = service_provider
        cache_options = self.__options.get('cache')
        # Event loop should already be registered in ServiceProvider by edge.from_options
        self.__event_loop = loop
        self.__cache_manager = CacheFactory.create(cache_options)
        self.__logger = logger

        self.name = self.__options.get('name')

        # Initialize WebSocket session manager
        self.__ws_manager = WebSocketSessionManager(
            on_message_receive_async=self.on_message_receive_async,
            heartbeat_interval=30.0
        )

        # Store listener factory for lazy loading in initialize_task
        self.__listener_factory = listener_factory
        self.__listeners: list[IListener] = []

        # Initialize ContextFactory - it handles all routing logic
        self.__context_factory = ContextFactory(
            dispatcher=self,
            options=options,
            lookup=self.__look_up
        )

    @property
    def Logger(self) -> ILogService:
        """Get logger service"""
        return self.__logger

    @property
    def service_provider(self) -> IServiceProvider:
        """Get the root service provider (DI container)"""
        return self.__service_provider

    # Properties for IDispatcher interface
    @property
    def options(self) -> AppOptions:
        """Get application configuration options (AppOptions = dict)"""
        return self.__options

    @property
    def cache_manager(self) -> 'CacheManager':
        """Get cache manager"""
        return self.__cache_manager

    def register_handler(
        self,
        context_type: Type['Context'],
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

        # Import context types at runtime to avoid circular imports
        from bclib.context import (ClientSourceContext,
                                   ClientSourceMemberContext, HttpContext,
                                   RabbitContext, RESTfulContext,
                                   ServerSourceContext,
                                   ServerSourceMemberContext, WebSocketContext)

        # Map context types to their decorator methods
        decorator_map = {
            RESTfulContext: self.restful_action,
            HttpContext: self.web_action,
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
        self.__context_factory.rebuild_router()

        return self

    def unregister_handler(
        self,
        context_type: Type['Context'],
        handler: Callable
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
            # Remove specific handler using CallbackInfo's matches_handler method
            handlers[:] = [
                callback_info for callback_info in handlers
                if not callback_info.matches_handler(handler)
            ]

        # Rebuild router if auto-generated
        self.__context_factory.rebuild_router()

        return self

    def restful_action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Decorator for RESTful action with automatic DI

        Context parameter is now optional - handler can choose to:
        - Accept context: def handler(context: RESTfulContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: RESTfulContext, logger: ILogger)

        Args:
            route: Optional URL route pattern as first argument (e.g., "users/:id", "api/posts")
            method: Optional HTTP method filter - single string ("get", "post") or list (["GET", "POST"])
            *predicates: Variable number of Predicate objects for additional request matching rules

        Example:
            ```python
            # Using route as first argument
            @app.restful_action("users/:id")
            def get_user(context: RESTfulContext):
                user_id = context.url_segments['id']
                return {"user_id": user_id}

            # Using route and single method
            @app.restful_action("users", method="post")
            def create_user(context: RESTfulContext):
                return {"status": "created"}

            # Using multiple methods as array
            @app.restful_action("users/:id", method=["GET", "PUT"])
            def user_handler(context: RESTfulContext):
                return {"user_id": context.url_segments['id']}

            # Using route with additional predicates
            @app.restful_action("posts/:id", method="GET", app.has_value("context.query.filter"))
            def get_filtered_post(context: RESTfulContext):
                return {"post_id": context.url_segments['id']}

            # No route, just predicates
            @app.restful_action(predicates=[app.equal("context.query.type", "admin")])
            def admin_handler(context: RESTfulContext):
                return {"admin": True}
            ```
        """
        from bclib.context import RESTfulContext
        from bclib.predicate import PredicateHelper

        # Build predicates using helper method
        combined_predicates = PredicateHelper.build_predicates(
            route,
            method=method,
            *predicates
        )

        def _decorator(restful_action_handler: Callable):
            # Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(restful_action_handler)

            @wraps(restful_action_handler)
            async def wrapper(context: RESTfulContext):
                # Execute pre-compiled plan (fast - no reflection)
                kwargs = {**(context.url_segments or {}),
                          **(context.query or {})}
                action_result = await injection_plan.execute_async(
                    self.__service_provider, self.__event_loop, **kwargs)
                return None if action_result is None else context.generate_response(action_result)

            self._get_context_lookup(RESTfulContext)\
                .append(CallbackInfo(combined_predicates, wrapper))
            return restful_action_handler
        return _decorator

    def web_action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Decorator for legacy web request action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: HttpContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: HttpContext, logger: ILogger)

        Args:
            route: Optional URL route pattern as first argument (e.g., "page/:id", "static/assets")
            method: Optional HTTP method filter - single string ("get", "post") or list (["GET", "POST"])
            *predicates: Variable number of Predicate objects for additional request matching rules

        Example:
            ```python
            # Using route as first argument
            @app.web_action("about")
            def about_page(context: HttpContext):
                return "<h1>About Us</h1>"

            # Using route and single method
            @app.web_action("contact", method="post")
            def submit_contact(context: HttpContext):
                return "<h1>Thank you!</h1>"

            # Using multiple methods as array
            @app.web_action("form", method=["GET", "POST"])
            def form_handler(context: HttpContext):
                return "<h1>Form Page</h1>"

            # Using route with additional predicates
            @app.web_action("admin/:section", method="GET", app.has_value("context.query.token"))
            def admin_panel(context: HttpContext):
                return f"<h1>Admin: {context.url_segments['section']}</h1>"

            # No route, just predicates
            @app.web_action(predicates=[app.callback(check_auth)])
            def protected_page(context: HttpContext):
                return "<h1>Protected</h1>"
            ```
        """
        from bclib.context import HttpContext
        from bclib.predicate import PredicateHelper

        # Build predicates using helper method
        combined_predicates = PredicateHelper.build_predicates(
            route,
            method=method,
            *predicates
        )

        def _decorator(web_action_handler: Callable):
            # Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(web_action_handler)

            @wraps(web_action_handler)
            async def wrapper(context: HttpContext):
                kwargs = context.url_segments if context.url_segments else {}
                action_result = await injection_plan.execute_async(self.__service_provider, self.__event_loop, **kwargs)
                return None if action_result is None else context.generate_response(action_result)

            self._get_context_lookup(HttpContext)\
                .append(CallbackInfo(combined_predicates, wrapper))
            return web_action_handler
        return _decorator

    def websocket_action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Decorator for WebSocket action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: WebSocketSession)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: WebSocketSession, logger: ILogger)

        Args:
            route: Optional URL route pattern (e.g., "ws/chat/:room")
            method: Optional HTTP method filter for WebSocket upgrade request
            *predicates: Variable number of Predicate objects for additional matching rules
        """
        from bclib.context import WebSocketContext
        from bclib.predicate import PredicateHelper

        # Build predicates using helper method
        combined_predicates = PredicateHelper.build_predicates(
            route,
            method=method,
            *predicates
        )

        def _decorator(websocket_action_handler: Callable):
            # Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(websocket_action_handler)

            @wraps(websocket_action_handler)
            async def wrapper(context: WebSocketContext):
                kwargs = context.url_segments if context.url_segments else {}
                return await injection_plan.execute_async(self.__service_provider, self.__event_loop, **kwargs)

            self._get_context_lookup(WebSocketContext)\
                .append(CallbackInfo(combined_predicates, wrapper))
            return websocket_action_handler
        return _decorator

    def client_source_action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Decorator for client source action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: ClientSourceContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: ClientSourceContext, logger: ILogger)

        Args:
            route: Optional URL route pattern (e.g., "data/users/:id")
            method: Optional HTTP method filter
            *predicates: Variable number of Predicate objects for additional matching rules
        """
        from bclib.context import (ClientSourceContext,
                                   ClientSourceMemberContext)
        from bclib.predicate import PredicateHelper

        # Build predicates using helper method
        combined_predicates = PredicateHelper.build_predicates(
            route,
            method=method,
            *predicates
        )

        def _decorator(client_source_action_handler: Callable):
            # Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(client_source_action_handler)

            @wraps(client_source_action_handler)
            async def wrapper(context):
                kwargs = context.url_segments if context.url_segments else {}
                data = await injection_plan.execute_async(self.__service_provider, self.__event_loop, **kwargs)
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
                .append(CallbackInfo(combined_predicates, wrapper))

            return client_source_action_handler
        return _decorator

    def client_source_member_action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Decorator for client source member action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: ClientSourceMemberContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: ClientSourceMemberContext, logger: ILogger)

        Args:
            route: Optional URL route pattern
            method: Optional HTTP method filter
            *predicates: Variable number of Predicate objects for additional matching rules
        """
        from bclib.context import ClientSourceMemberContext
        from bclib.predicate import PredicateHelper

        # Build predicates using helper method
        combined_predicates = PredicateHelper.build_predicates(
            route,
            method=method,
            *predicates
        )

        def _decorator(client_source_member_handler: Callable):
            # Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(client_source_member_handler)

            @wraps(client_source_member_handler)
            async def wrapper(context: ClientSourceMemberContext):
                kwargs = context.url_segments if context.url_segments else {}
                return await injection_plan.execute_async(self.__service_provider, self.__event_loop, **kwargs)

            self._get_context_lookup(ClientSourceMemberContext)\
                .append(CallbackInfo(combined_predicates, wrapper))
            return client_source_member_handler
        return _decorator

    def server_source_action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Decorator for server source action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: ServerSourceContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: ServerSourceContext, logger: ILogger)

        Args:
            route: Optional URL route pattern
            method: Optional HTTP method filter
            *predicates: Variable number of Predicate objects for additional matching rules
        """
        from bclib.context import (ServerSourceContext,
                                   ServerSourceMemberContext)
        from bclib.predicate import PredicateHelper

        # Build predicates using helper method
        combined_predicates = PredicateHelper.build_predicates(
            route,
            method=method,
            *predicates
        )

        def _decorator(server_source_action_handler: Callable):
            # Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(server_source_action_handler)

            @wraps(server_source_action_handler)
            async def wrapper(context: ServerSourceContext):
                kwargs = context.url_segments if context.url_segments else {}
                data = await injection_plan.execute_async(self.__service_provider, self.__event_loop, **kwargs)
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
                .append(CallbackInfo(combined_predicates, wrapper))

            return server_source_action_handler
        return _decorator

    def server_source_member_action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Decorator for server source member action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: ServerSourceMemberContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: ServerSourceMemberContext, logger: ILogger)

        Args:
            route: Optional URL route pattern
            method: Optional HTTP method filter
            *predicates: Variable number of Predicate objects for additional matching rules
        """
        from bclib.context import ServerSourceMemberContext
        from bclib.predicate import PredicateHelper

        # Build predicates using helper method
        combined_predicates = PredicateHelper.build_predicates(
            route,
            method=method,
            *predicates
        )

        def _decorator(server_source_member_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(server_source_member_action_handler)

            @wraps(server_source_member_action_handler)
            async def wrapper(context):
                kwargs = context.url_segments if context.url_segments else {}
                return await injection_plan.execute_async(self.__service_provider, self.__event_loop, **kwargs)

            self._get_context_lookup(ServerSourceMemberContext)\
                .append(CallbackInfo(combined_predicates, wrapper))
            return server_source_member_action_handler
        return _decorator

    def rabbit_action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Decorator for RabbitMQ message action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: RabbitContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: RabbitContext, logger: ILogger)

        Args:
            route: Optional URL route pattern
            method: Optional HTTP method filter
            *predicates: Variable number of Predicate objects for additional matching rules
        """
        from bclib.context import RabbitContext
        from bclib.predicate import PredicateHelper

        # Build predicates using helper method
        combined_predicates = PredicateHelper.build_predicates(
            route,
            method=method,
            *predicates
        )

        def _decorator(rabbit_action_handler: Callable):
            # ✨ Pre-compile injection plan at decoration time (once)
            injection_plan = InjectionPlan(rabbit_action_handler)

            @wraps(rabbit_action_handler)
            async def wrapper(context):
                kwargs = context.url_segments if context.url_segments else {}
                return await injection_plan.execute_async(self.__service_provider, self.__event_loop, **kwargs)

            self._get_context_lookup(RabbitContext)\
                .append(CallbackInfo(combined_predicates, wrapper))

            return rabbit_action_handler
        return _decorator

    def action(self, route: str = None, method: 'str | list[str]' = None, *predicates: (Predicate)):
        """
        Universal action decorator that automatically determines the action type based on handler's context parameter

        This decorator inspects the handler's signature to find the context type parameter and automatically
        routes to the appropriate specific action decorator (web_action, restful_action, websocket_action, etc.).

        Args:
            route: Optional URL route pattern
            method: Optional HTTP method filter - single string or list
            *predicates: Variable number of Predicate objects for additional matching rules

        Returns:
            The appropriate decorator based on the handler's context type

        Example:
            ```python
            # Automatically uses restful_action because context is RESTfulContext
            @app.action("users/:id", method="GET")
            def get_user(context: RESTfulContext):
                return {"user_id": context.url_segments['id']}

            # Automatically uses web_action because context is HttpContext
            @app.action("home", method="GET")
            def home_page(context: HttpContext):
                return "<h1>Home Page</h1>"

            # Automatically uses websocket_action because context is WebSocketContext
            @app.action("ws/chat/:room")
            async def chat_handler(context: WebSocketContext):
                await context.send_text(f"Welcome to room {context.url_segments['room']}")

            # Works without context parameter too (inspects other type hints)
            @app.action("api/data")
            def get_data():
                return {"data": "value"}
            ```

        Note:
            The decorator determines the action type by inspecting the handler's type hints.
            If no context type is found, it defaults to restful_action.
        """
        from typing import get_type_hints

        from bclib.context import (ClientSourceContext,
                                   ClientSourceMemberContext, HttpContext,
                                   RabbitContext, RESTfulContext,
                                   ServerSourceContext,
                                   ServerSourceMemberContext, WebSocketContext)

        def _universal_decorator(handler: Callable):
            # Inspect handler to determine context type
            try:
                type_hints = get_type_hints(handler)
                context_type = None

                # Check all parameters for a context type
                for param_name, param_type in type_hints.items():
                    if param_type in (HttpContext, RESTfulContext, WebSocketContext,
                                      ClientSourceContext, ClientSourceMemberContext,
                                      ServerSourceContext, ServerSourceMemberContext,
                                      RabbitContext):
                        context_type = param_type
                        break

                # If no context type found in parameters, check handler name
                if context_type is None:
                    handler_name = handler.__name__.lower()

                    # Map context keywords to context types
                    if 'http' in handler_name or 'web' in handler_name:
                        context_type = HttpContext
                    elif 'restful' in handler_name or 'rest' in handler_name or 'api' in handler_name:
                        context_type = RESTfulContext
                    elif 'websocket' in handler_name or 'ws' in handler_name:
                        context_type = WebSocketContext
                    elif 'clientsourcemember' in handler_name:
                        context_type = ClientSourceMemberContext
                    elif 'clientsource' in handler_name:
                        context_type = ClientSourceContext
                    elif 'serversourcemember' in handler_name:
                        context_type = ServerSourceMemberContext
                    elif 'serversource' in handler_name:
                        context_type = ServerSourceContext
                    elif 'rabbit' in handler_name or 'mq' in handler_name:
                        context_type = RabbitContext

                # Route to appropriate decorator based on context type
                if context_type == HttpContext:
                    return self.web_action(route, method, *predicates)(handler)
                elif context_type == RESTfulContext:
                    return self.restful_action(route, method, *predicates)(handler)
                elif context_type == WebSocketContext:
                    return self.websocket_action(route, method, *predicates)(handler)
                elif context_type == ClientSourceContext:
                    return self.client_source_action(route, method, *predicates)(handler)
                elif context_type == ClientSourceMemberContext:
                    return self.client_source_member_action(route, method, *predicates)(handler)
                elif context_type == ServerSourceContext:
                    return self.server_source_action(route, method, *predicates)(handler)
                elif context_type == ServerSourceMemberContext:
                    return self.server_source_member_action(route, method, *predicates)(handler)
                elif context_type == RabbitContext:
                    return self.rabbit_action(route, method, *predicates)(handler)
                else:
                    # Default to restful_action if no context type found
                    return self.restful_action(route, method, *predicates)(handler)

            except Exception:
                # If type hint inspection fails, default to restful_action
                return self.restful_action(route, method, *predicates)(handler)

        return _universal_decorator

    def _get_context_lookup(self, key: Type) -> 'list[CallbackInfo]':
        """Get key related action list object"""

        ret_val: None
        if key in self.__look_up:
            ret_val = self.__look_up[key]
        else:
            ret_val = list()
            self.__look_up[key] = ret_val
        return ret_val

    async def dispatch_async(self, context: 'Context') -> dict:
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
                raise HandlerNotFoundErr(context_type.__name__)
        except Exception as ex:
            if self.__logger.log_error:
                traceback.print_exc()
            result = context.generate_error_response(ex)
        return result

    def dispatch_in_background(self, context: 'Context') -> asyncio.Future:
        """Dispatch context in background"""

        return self.__event_loop.create_task(self.dispatch_async(context))

    async def on_message_receive_async(self, message: Message) -> None:
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
        try:
            context = self.__context_factory.create_context(message)
            response = await self.dispatch_async(context)
            if isinstance(message, IResponseBaseMessage):
                await message.set_response_async(response)
        except Exception as ex:
            print(f"Error in process received message {ex}")
            raise ex

    @property
    def ws_manager(self) -> WebSocketSessionManager:
        """Get WebSocket session manager"""
        return self.__ws_manager

    def run_in_background(self, callback: 'Callable|Coroutine', *args: Any) -> asyncio.Future:
        """Execute function or coroutine in background"""
        if inspect.iscoroutinefunction(callback):
            return self.__event_loop.create_task(callback(*args))
        else:
            return self.__event_loop.run_in_executor(None, callback, *args)

    def add_listener(self, listener: IListener):
        """Add a listener to the dispatcher

        Args:
            listener: Listener instance implementing IListener interface
        """
        self.__listeners.append(listener)

    def initialize_task(self):
        """Initialize all listeners and tasks

        Loads listeners from factory and initializes them. This includes HTTP, WebSocket, 
        TCP, and RabbitMQ listeners based on application configuration.
        """
        # Ensure router is ready before server starts
        self.__context_factory.rebuild_router()

        # Load listeners from factory if not already loaded
        if not self.__listeners:
            self.__listeners = self.__listener_factory.load_listeners(self)

        # Initialize all listeners (HTTP, Socket, Rabbit, etc.)
        for listener in self.__listeners:
            listener.initialize_task(self.__event_loop)

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

            self.__event_loop.create_task(start_endpoint_server())

    def listening(self, before_start: Coroutine = None, after_end: Coroutine = None, with_block: bool = True):
        """Start listening to request for process"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda sig, _: self.__event_loop.stop())
        if before_start != None:
            self.__event_loop.run_until_complete(
                self.__event_loop.create_task(before_start()))
        self.initialize_task()
        if with_block:
            self.__event_loop.run_forever()
            tasks = asyncio.all_tasks(loop=self.__event_loop)
            for task in tasks:
                task.cancel()
            group = asyncio.gather(*tasks, return_exceptions=True)
            self.__event_loop.run_until_complete(group)
            if after_end != None:
                self.__event_loop.run_until_complete(
                    self.__event_loop.create_task(after_end()))
            self.__event_loop.close()

    def add_static_handler(self, handler: StaticFileHandler) -> None:
        """Add static file handler to dispatcher"""
        from bclib.context import HttpContext

        async def async_wrapper(context):
            action_result = await handler.handle(context)
            return None if action_result is None else context.generate_response(action_result)

        self._get_context_lookup(HttpContext)\
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
