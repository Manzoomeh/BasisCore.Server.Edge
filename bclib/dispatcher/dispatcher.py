"""Base class for dispatching request"""
import asyncio
import inspect
import signal
import sys
import traceback
from abc import ABC
from functools import wraps
from typing import Any, Callable, Coroutine, Optional

from bclib.cache import CacheFactory
from bclib.context import (ClientSourceContext, ClientSourceMemberContext,
                           Context, RabbitContext, RESTfulContext,
                           ServerSourceContext, ServerSourceMemberContext,
                           SocketContext, WebContext, WebSocketContext)
from bclib.db_manager import DbManager
from bclib.exception import HandlerNotFoundErr
from bclib.listener import RabbitBusListener
from bclib.logger import ILogger, LoggerFactory, LogObject
from bclib.predicate import Predicate
from bclib.utility import DictEx
from bclib.utility.static_file_handler import StaticFileHandler

from ..dispatcher.callback_info import CallbackInfo


class Dispatcher(ABC):
    """Base class for dispatching request"""

    def __init__(self, options: dict = None, loop: asyncio.AbstractEventLoop = None):
        self.options = DictEx(options)
        self.__look_up: 'dict[str, list[CallbackInfo]]' = dict()
        cache_options = self.options.cache if "cache" in self.options else None
        if loop is None and sys.platform == 'win32':
            # By default Windows can use only 64 sockets in asyncio loop. This is a limitation of underlying select() API call.
            # Use Windows version of proactor event loop using IOCP
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
        self.event_loop = asyncio.get_event_loop() if loop is None else loop
        self.cache_manager = CacheFactory.create(cache_options)
        self.db_manager = DbManager(self.options, self.event_loop)
        self.__logger: ILogger = LoggerFactory.create(self.options)
        self.log_error: bool = self.options.log_error if self.options.has(
            "log_error") else False
        self.log_request: bool = self.options.log_request if self.options.has(
            "log_request") else True
        self.__rabbit_dispatcher: 'list[RabbitBusListener]' = list()
        if "router" in self.options and "rabbit" in self.options.router:
            for setting in self.options.router.rabbit:
                self.__rabbit_dispatcher.append(
                    RabbitBusListener(setting, self))

    def _inject_from_context(self, handler: Callable, context: Context) -> dict:
        """
        Helper method to inject dependencies from context's service provider

        Args:
            handler: The handler function
            context: The request context with services

        Returns:
            Dictionary of injected dependencies
        """
        if hasattr(context, 'services') and context.services:
            return context.services.inject_dependencies(handler, context)
        return {}

    def socket_action(self, * predicates: (Predicate)):
        """Decorator for determine Socket action with automatic DI"""

        def _decorator(socket_action_handler: 'Callable[[SocketContext],bool]'):

            @wraps(socket_action_handler)
            async def non_async_wrapper(context: SocketContext):
                injected_kwargs = self._inject_from_context(
                    socket_action_handler, context)
                await self.event_loop.run_in_executor(None, socket_action_handler, context, **injected_kwargs)
                return True

            @wraps(socket_action_handler)
            async def async_wrapper(context: SocketContext):
                injected_kwargs = self._inject_from_context(
                    socket_action_handler, context)
                await socket_action_handler(context, **injected_kwargs)
                return True

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                socket_action_handler) else non_async_wrapper

            self._get_context_lookup(SocketContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return socket_action_handler
        return _decorator

    def restful_action(self, * predicates: (Predicate)):
        """Decorator for determine RESTful action with automatic DI"""

        def _decorator(restful_action_handler: 'Callable[[RESTfulContext], dict]'):

            @wraps(restful_action_handler)
            async def non_async_wrapper(context: RESTfulContext):
                injected_kwargs = self._inject_from_context(
                    restful_action_handler, context)
                action_result = await self.event_loop.run_in_executor(
                    None, restful_action_handler, context, **injected_kwargs
                )
                return None if action_result is None else context.generate_response(action_result)

            @wraps(restful_action_handler)
            async def async_wrapper(context: RESTfulContext):
                injected_kwargs = self._inject_from_context(
                    restful_action_handler, context)
                action_result = await restful_action_handler(context, **injected_kwargs)
                return None if action_result is None else context.generate_response(action_result)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                restful_action_handler) else non_async_wrapper

            self._get_context_lookup(RESTfulContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return restful_action_handler
        return _decorator

    def web_action(self, * predicates: (Predicate)):
        """Decorator for determine legacy web request action with automatic DI"""

        def _decorator(web_action_handler: 'Callable[[WebContext], str]'):

            @wraps(web_action_handler)
            async def non_async_wrapper(context: WebContext):
                injected_kwargs = self._inject_from_context(
                    web_action_handler, context)
                action_result = await self.event_loop.run_in_executor(
                    None, web_action_handler, context, **injected_kwargs
                )
                return None if action_result is None else context.generate_response(action_result)

            @wraps(web_action_handler)
            async def async_wrapper(context: WebContext):
                injected_kwargs = self._inject_from_context(
                    web_action_handler, context)
                action_result = await web_action_handler(context, **injected_kwargs)
                return None if action_result is None else context.generate_response(action_result)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                web_action_handler) else non_async_wrapper

            self._get_context_lookup(WebContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return web_action_handler
        return _decorator

    def websocket_action(self, * predicates: (Predicate)):
        """Decorator for WebSocket action with automatic DI"""

        def _decorator(websocket_action_handler: 'Callable[[Any, Any], None]'):
            from bclib.dispatcher.websocket_session import WebSocketSession

            @wraps(websocket_action_handler)
            async def non_async_wrapper(context: WebSocketSession):
                injected_kwargs = self._inject_from_context(
                    websocket_action_handler, context)
                return await self.event_loop.run_in_executor(None, websocket_action_handler, context, **injected_kwargs)

            @wraps(websocket_action_handler)
            async def async_wrapper(context: WebSocketSession):
                injected_kwargs = self._inject_from_context(
                    websocket_action_handler, context)
                return await websocket_action_handler(context, **injected_kwargs)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                websocket_action_handler) else non_async_wrapper

            self._get_context_lookup(WebSocketContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return websocket_action_handler
        return _decorator

    def client_source_action(self, *predicates: (Predicate)):
        """Decorator for determine source action with automatic DI"""

        def _decorator(client_source_action_handler: 'Callable[[ClientSourceContext], Any]'):
            @wraps(client_source_action_handler)
            async def non_async_wrapper(context: ClientSourceContext):
                injected_kwargs = self._inject_from_context(
                    client_source_action_handler, context)
                data = await self.event_loop.run_in_executor(None, client_source_action_handler, context, **injected_kwargs)
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

            @wraps(client_source_action_handler)
            async def async_wrapper(context: ClientSourceContext):
                injected_kwargs = self._inject_from_context(
                    client_source_action_handler, context)
                data = await client_source_action_handler(context, **injected_kwargs)
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

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                client_source_action_handler) else non_async_wrapper

            self._get_context_lookup(ClientSourceContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))

            return client_source_action_handler
        return _decorator

    def client_source_member_action(self, *predicates: (Predicate)):
        """Decorator for determine source member action method with automatic DI"""

        def _decorator(client_source_member_handler: 'Callable[[ClientSourceMemberContext], Any]'):

            @wraps(client_source_member_handler)
            async def non_async_wrapper(context: WebContext):
                injected_kwargs = self._inject_from_context(
                    client_source_member_handler, context)
                return await self.event_loop.run_in_executor(None, client_source_member_handler, context, **injected_kwargs)

            @wraps(client_source_member_handler)
            async def async_wrapper(context: WebContext):
                injected_kwargs = self._inject_from_context(
                    client_source_member_handler, context)
                return await client_source_member_handler(context, **injected_kwargs)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                client_source_member_handler) else non_async_wrapper

            self._get_context_lookup(ClientSourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return client_source_member_handler
        return _decorator

    def server_source_action(self, *predicates: (Predicate)):
        """Decorator for determine source action with automatic DI"""

        def _decorator(server_source_action_handler: 'Callable[[ServerSourceContext], Any]'):
            @wraps(server_source_action_handler)
            async def non_async_wrapper(context: ServerSourceContext):
                injected_kwargs = self._inject_from_context(
                    server_source_action_handler, context)
                data = await self.event_loop.run_in_executor(None, server_source_action_handler, context, **injected_kwargs)
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

            @wraps(server_source_action_handler)
            async def async_wrapper(context: ServerSourceContext):
                injected_kwargs = self._inject_from_context(
                    server_source_action_handler, context)
                data = await server_source_action_handler(context, **injected_kwargs)
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

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                server_source_action_handler) else non_async_wrapper

            self._get_context_lookup(ServerSourceContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))

            return server_source_action_handler
        return _decorator

    def server_source_member_action(self, *predicates: (Predicate)):
        """Decorator for determine server source member action method with automatic DI"""

        def _decorator(server_source_member_action_handler: 'Callable[[ServerSourceMemberContext], Any]'):

            @wraps(server_source_member_action_handler)
            async def non_async_wrapper(context: WebContext):
                injected_kwargs = self._inject_from_context(
                    server_source_member_action_handler, context)
                return await self.event_loop.run_in_executor(None, server_source_member_action_handler, context, **injected_kwargs)

            @wraps(server_source_member_action_handler)
            async def async_wrapper(context: WebContext):
                injected_kwargs = self._inject_from_context(
                    server_source_member_action_handler, context)
                return await server_source_member_action_handler(context, **injected_kwargs)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                server_source_member_action_handler) else non_async_wrapper

            self._get_context_lookup(ServerSourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return server_source_member_action_handler
        return _decorator

    def rabbit_action(self, * predicates: (Predicate)):
        """Decorator for determine rabbit-mq message request action with automatic DI"""

        def _decorator(rabbit_action_handler: 'Callable[[RabbitContext], bool]'):

            @wraps(rabbit_action_handler)
            async def non_async_wrapper(context: RabbitContext):
                injected_kwargs = self._inject_from_context(
                    rabbit_action_handler, context)
                return await self.event_loop.run_in_executor(None, rabbit_action_handler, context, **injected_kwargs)

            @wraps(rabbit_action_handler)
            async def async_wrapper(context: RabbitContext):
                injected_kwargs = self._inject_from_context(
                    rabbit_action_handler, context)
                return await rabbit_action_handler(context, **injected_kwargs)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                rabbit_action_handler) else non_async_wrapper

            self._get_context_lookup(RabbitContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))

            return rabbit_action_handler
        return _decorator

    def _get_context_lookup(self, key: str) -> 'list[CallbackInfo]':
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
        name = type(context).__name__
        try:
            items = self._get_context_lookup(name)
            for item in items:
                result = await item.try_execute_async(context)
                if result is not None:
                    break
            else:
                ex = HandlerNotFoundErr(name)
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

    def initialize_task(self):
        for dispatcher in self.__rabbit_dispatcher:
            dispatcher.initialize_task(self.event_loop)

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

        self._get_context_lookup(WebContext.__name__)\
            .append(CallbackInfo([], async_wrapper))
