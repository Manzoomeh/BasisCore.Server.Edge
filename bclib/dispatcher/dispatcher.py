"""Base class for dispatching request"""
import asyncio
import inspect
from abc import ABC
import signal
from typing import Awaitable, Callable, Any, Coroutine, Optional, TYPE_CHECKING
from functools import wraps
from dependency_injector import containers

from bclib.logger.ilogger import ILogger
from cache.cache_manager import CacheManager
from bclib.predicate import Predicate
from bclib.db_manager.db_manager import DbManager
from bclib.utility import DictEx
from bclib.exception import HandlerNotFoundErr
from bclib.dispatcher.callback_info import CallbackInfo

from bclib.context.client_source_context import ClientSourceContext
from bclib.context.client_source_member_context import ClientSourceMemberContext
from bclib.context.context import Context
from bclib.context.restful_context import RESTfulContext
from bclib.context.web_context import WebContext
from bclib.context.rabbit_context import RabbitContext
from bclib.context.socket_context import SocketContext
from bclib.context.server_source_context import ServerSourceContext
from bclib.context.server_source_member_context import ServerSourceMemberContext
from bclib.context.end_point_context import EndPointContext

if TYPE_CHECKING:
    from bclib.logger.ilogger import LogObject


class Dispatcher(ABC):
    """Base class for dispatching request"""

    def __init__(self, container: 'containers.Container',  options: 'DictEx', cache_manager: 'CacheManager', db_manager: 'DbManager', logger: 'ILogger', loop: 'asyncio.AbstractEventLoop'):
        self.options = options
        self.container = container
        self.__look_up: 'dict[str, list[CallbackInfo]]' = dict()
        self.event_loop: 'asyncio.AbstractEventLoop' = loop
        self.cache_manager: 'CacheManager' = cache_manager
        self.db_manager = db_manager
        self.logger: ILogger = logger
        self.__rabbit_dispatcher: 'list[RabbitBusListener]' = list()
        if "router" in self.options and "rabbit" in self.options.router:
            for setting in self.options.router.rabbit:
                self.__rabbit_dispatcher.append(
                    RabbitBusListener(setting, self))

    def endpoint_action(self, * predicates: (Predicate)):
        """Decorator for determine end point action"""

        def _decorator(end_point_action_handler: 'Callable[[EndPointContext],bool]'):

            @wraps(end_point_action_handler)
            async def non_async_wrapper(context: 'EndPointContext'):
                await self.event_loop.run_in_executor(None, end_point_action_handler, context)
                return True

            @wraps(end_point_action_handler)
            async def async_wrapper(context: 'EndPointContext'):
                await end_point_action_handler(context)
                return True

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                end_point_action_handler) else non_async_wrapper

            self._get_context_lookup(EndPointContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return end_point_action_handler
        return _decorator

    def socket_action(self, * predicates: (Predicate)):
        """Decorator for determine Socket action"""

        def _decorator(socket_action_handler: 'Callable[[SocketContext],bool]'):

            @wraps(socket_action_handler)
            async def non_async_wrapper(context: 'SocketContext'):
                await self.event_loop.run_in_executor(None, socket_action_handler, context)
                return True

            @wraps(socket_action_handler)
            async def async_wrapper(context: 'SocketContext'):
                await socket_action_handler(context)
                return True

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                socket_action_handler) else non_async_wrapper

            self._get_context_lookup(SocketContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return socket_action_handler
        return _decorator

    def restful_action(self, * predicates: (Predicate)):
        """Decorator for determine RESTful action"""

        def _decorator(restful_action_handler: 'Callable[[RESTfulContext], dict]'):

            @wraps(restful_action_handler)
            async def non_async_wrapper(context: 'RESTfulContext'):
                action_result = await self.event_loop.run_in_executor(None, restful_action_handler, context)
                return None if action_result is None else context.generate_response(action_result)

            @wraps(restful_action_handler)
            async def async_wrapper(context: 'RESTfulContext'):
                action_result = await restful_action_handler(context)
                return None if action_result is None else context.generate_response(action_result)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                restful_action_handler) else non_async_wrapper

            self._get_context_lookup(RESTfulContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return restful_action_handler
        return _decorator

    def web_action(self, * predicates: (Predicate)):
        """Decorator for determine legacy web request action"""

        def _decorator(web_action_handler: 'Callable[[WebContext], str]'):

            @wraps(web_action_handler)
            async def non_async_wrapper(context: 'WebContext'):
                action_result = await self.event_loop.run_in_executor(None, web_action_handler, context)
                return None if action_result is None else context.generate_response(action_result)

            @wraps(web_action_handler)
            async def async_wrapper(context: 'WebContext'):
                action_result = await web_action_handler(context)
                return None if action_result is None else context.generate_response(action_result)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                web_action_handler) else non_async_wrapper

            self._get_context_lookup(WebContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return web_action_handler
        return _decorator

    def client_source_action(self, *predicates: (Predicate)):
        """Decorator for determine source action"""

        def _decorator(client_source_action_handler: 'Callable[[ClientSourceContext], Any]'):
            @wraps(client_source_action_handler)
            async def non_async_wrapper(context: 'ClientSourceContext'):
                data = await self.event_loop.run_in_executor(None, client_source_action_handler, context)
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
            async def async_wrapper(context: 'ClientSourceContext'):
                data = await client_source_action_handler(context)
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
        """Decorator for determine source member action method"""

        def _decorator(client_source_member_handler: 'Callable[[ClientSourceMemberContext], Any]'):

            @wraps(client_source_member_handler)
            async def non_async_wrapper(context: 'WebContext'):
                return await self.event_loop.run_in_executor(None, client_source_member_handler, context)

            @wraps(client_source_member_handler)
            async def async_wrapper(context: 'WebContext'):
                return await client_source_member_handler(context)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                client_source_member_handler) else non_async_wrapper

            self._get_context_lookup(ClientSourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return client_source_member_handler
        return _decorator

    def server_source_action(self, *predicates: (Predicate)):
        """Decorator for determine source action"""

        def _decorator(server_source_action_handler: 'Callable[[ServerSourceContext], Any]'):
            @wraps(server_source_action_handler)
            async def non_async_wrapper(context: 'ServerSourceContext'):
                data = await self.event_loop.run_in_executor(None, server_source_action_handler, context)
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
            async def async_wrapper(context: 'ServerSourceContext'):
                data = await server_source_action_handler(context)
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
        """Decorator for determine server source member action method"""

        def _decorator(server_source_member_action_handler: 'Callable[[ServerSourceMemberContext], Any]'):

            @wraps(server_source_member_action_handler)
            async def non_async_wrapper(context: 'WebContext'):
                return await self.event_loop.run_in_executor(None, server_source_member_action_handler, context)

            @wraps(server_source_member_action_handler)
            async def async_wrapper(context: 'WebContext'):
                return await server_source_member_action_handler(context)

            wrapper = async_wrapper if inspect.iscoroutinefunction(
                server_source_member_action_handler) else non_async_wrapper

            self._get_context_lookup(ServerSourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], wrapper))
            return server_source_member_action_handler
        return _decorator

    def rabbit_action(self, * predicates: (Predicate)):
        """Decorator for determine rabbit-mq message request action"""

        def _decorator(rabbit_action_handler: 'Callable[[RabbitContext], bool]'):

            @wraps(rabbit_action_handler)
            async def non_async_wrapper(context: 'RabbitContext'):
                return await self.event_loop.run_in_executor(None, rabbit_action_handler, context)

            @wraps(rabbit_action_handler)
            async def async_wrapper(context: 'RabbitContext'):
                return await rabbit_action_handler(context)

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

    async def dispatch_async(self, context: 'Context') -> Any:
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
                self.logger.log_error(ex)
                result = context.generate_error_response(ex)
        except Exception as ex:
            self.logger.log_error(ex)
            result = context.generate_error_response(ex)
        return result

    def dispatch_in_background(self, context: 'Context') -> asyncio.Future:
        """Dispatch context in background"""

        return self.event_loop.create_task(self.dispatch_async(context))

    def initialize_task(self):
        for dispatcher in self.__rabbit_dispatcher:
            dispatcher.initialize_task(self.event_loop)

    # TODO:pre ansd post callback replaced with resource provider of DI
    def listening(self, with_block: bool = True):
        """Start listening to request for process"""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, lambda sig, _: self.event_loop.stop())
        init_process = self.container.init_resources()
        if isinstance(init_process, Awaitable):
            self.event_loop.run_until_complete(init_process)
        self.initialize_task()
        if with_block:
            self.event_loop.run_forever()
            tasks = asyncio.all_tasks(loop=self.event_loop)
            for task in tasks:
                task.cancel()
            group = asyncio.gather(*tasks, return_exceptions=True)
            self.event_loop.run_until_complete(group)
            shutdown_process = self.container.shutdown_resources()
            if isinstance(shutdown_process, Awaitable):
                self.event_loop.run_until_complete(shutdown_process)
            self.event_loop.close()

    def new_object_log(self, schema_name: str, routing_key: Optional[str] = None, **kwargs) -> 'LogObject':
        return self.logger.new_object_log(schema_name, routing_key, **kwargs)

    async def log_async(self, log_object: 'LogObject' = None, **kwargs):
        """log params"""
        if log_object is None:
            if "schema_name" not in kwargs:
                raise Exception("'schema_name' not set for apply logging!")
            schema_name = kwargs.pop("schema_name")
            log_object = self.new_object_log(schema_name, **kwargs)
        await self.logger.log_async(log_object)

    def log_in_background(self, log_object: 'LogObject' = None, **kwargs) -> Coroutine:
        """log params in background precess"""
        return self.event_loop.create_task(
            self.log_async(log_object, **kwargs)
        )
