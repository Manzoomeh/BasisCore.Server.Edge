"""Base class for dispatching request"""
import asyncio
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
from bclib.utility.service_provider import ServiceProvider
from bclib.utility.static_file_handler import StaticFileHandler

from ..dispatcher.callback_info import CallbackInfo


class Dispatcher(ABC):
    """Base class for dispatching request"""

    def __init__(self, options: dict = None, loop: asyncio.AbstractEventLoop = None):
        self.options = DictEx(options)
        self.__look_up: 'dict[str, list[CallbackInfo]]' = dict()
        self.__service_provider = ServiceProvider()
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

    @property
    def services(self) -> ServiceProvider:
        """Get the service provider (DI container)"""
        return self.__service_provider

    def socket_action(self, * predicates: (Predicate)):
        """
        Decorator for Socket action with automatic DI

        Context parameter is optional - handler can choose to:
        - Accept context: def handler(context: SocketContext)
        - Skip context and use only services: def handler(logger: ILogger)
        - Mix both: def handler(context: SocketContext, logger: ILogger)
        """

        def _decorator(socket_action_handler: Callable):

            @wraps(socket_action_handler)
            async def wrapper(context: SocketContext):
                await context.services.invoke_in_executor(socket_action_handler, self.event_loop)
                return True

            self._get_context_lookup(SocketContext.__name__)\
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

            @wraps(restful_action_handler)
            async def wrapper(context: RESTfulContext):
                action_result = await context.services.invoke_in_executor(restful_action_handler, self.event_loop)
                return None if action_result is None else context.generate_response(action_result)

            self._get_context_lookup(RESTfulContext.__name__)\
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

            @wraps(web_action_handler)
            async def wrapper(context: WebContext):
                action_result = await context.services.invoke_in_executor(web_action_handler, self.event_loop)
                return None if action_result is None else context.generate_response(action_result)

            self._get_context_lookup(WebContext.__name__)\
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

            @wraps(websocket_action_handler)
            async def wrapper(context: WebSocketSession):
                return await context.services.invoke_in_executor(websocket_action_handler, self.event_loop)

            self._get_context_lookup(WebSocketContext.__name__)\
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
            @wraps(client_source_action_handler)
            async def wrapper(context: ClientSourceContext):
                data = await context.services.invoke_in_executor(client_source_action_handler, self.event_loop)
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

            self._get_context_lookup(ClientSourceContext.__name__)\
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

            @wraps(client_source_member_handler)
            async def wrapper(context: WebContext):
                return await context.services.invoke_in_executor(client_source_member_handler, self.event_loop)

            self._get_context_lookup(ClientSourceMemberContext.__name__)\
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
            @wraps(server_source_action_handler)
            async def wrapper(context: ServerSourceContext):
                data = await context.services.invoke_in_executor(server_source_action_handler, self.event_loop)
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

            self._get_context_lookup(ServerSourceContext.__name__)\
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

            @wraps(server_source_member_action_handler)
            async def wrapper(context: WebContext):
                return await context.services.invoke_in_executor(server_source_member_action_handler, self.event_loop)

            self._get_context_lookup(ServerSourceMemberContext.__name__)\
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

            @wraps(rabbit_action_handler)
            async def wrapper(context: RabbitContext):
                return await context.services.invoke_in_executor(rabbit_action_handler, self.event_loop)

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
