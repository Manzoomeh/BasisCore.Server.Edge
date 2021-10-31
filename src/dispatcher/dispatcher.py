"""Base class for dispaching request"""
from typing import Callable, Any
from datetime import timedelta, datetime
from functools import wraps
from predicate import Predicate, InList, Equal
from context import SourceContext, SourceMemberContext, Context
from .callback_info import CallbackInfo


class Dispatcher:
    """Base class for dispaching request"""

    def __init__(self):
        self.__look_up: dict[str, list[CallbackInfo]] = dict()
        self.__cache_list: dict[str, list[Callable]] = dict()

    def source_action(self, *predicates: (Predicate)):
        """Decorator for determine source action"""
        def _decorator(source_action: Callable[[SourceContext], list]):
            @wraps(source_action)
            def _wrapper(context: SourceContext):
                data = source_action(context)
                result_set = list()
                if data is not None:
                    for member in context.command.member:
                        member_context = SourceMemberContext(
                            context, data, member)
                        dispath_result = self.dispatch(member_context)
                        result = {
                            "options": {
                                "tableName": member_context.table_name,
                                "keyFieldName": member_context.key_field_name,
                                "statusFieldName": member_context.status_field_name,
                                "mergeType": member_context.merge_type.value[0]
                            },
                            "data": dispath_result
                        }
                        result_set.append(result)
                return result_set
            self._get_context_lookup(SourceContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def source_member_action(self, *predicates: (Predicate)):
        """Decorator for determine source member action methode"""
        def _decorator(function: Callable[[SourceMemberContext], list]):

            @wraps(function)
            def _wrapper(context: SourceMemberContext):
                return function(context)

            self._get_context_lookup(SourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def _get_context_lookup(self, key: str) -> list[CallbackInfo]:
        """Get key related action list object"""
        ret_val: None
        if key in self.__look_up:
            ret_val = self.__look_up[key]
        else:
            ret_val = list()
            self.__look_up[key] = ret_val
        return ret_val

    def dispatch(self, context: Context) -> Any:
        """Dispatch context and get result from related action methode"""
        result: Any = None
        name = type(context).__name__
        items = self._get_context_lookup(name)
        for item in items:
            result = item.try_execute(context)
            if result is not None:
                break
        return result

    @staticmethod
    def in_list(expression: str, *items) -> Predicate:
        """Create list cheking predicate"""
        return InList(expression,  *items)

    @staticmethod
    def equal(expression: str, value) -> Predicate:
        """Create equality cheking predicate"""
        return Equal(expression, value)

    def cache(self, seconds: int = 0, key: str = None):
        """Cache result of function for seconds of time or until signal by key for clear"""
        def decorator(function):
            function.cache = None
            if seconds > 0:
                function.lifetime = timedelta(seconds=seconds)
                function.expiration = datetime.utcnow() + function.lifetime
            if key is not None:
                if key not in self.__cache_list:
                    self.__cache_list[key] = list()
                self.__cache_list[key].append(function)

            @wraps(function)
            def wrapper_with_time(*args, **kwargs):
                if function.cache is not None and datetime.utcnow() >= function.expiration:
                    function.cache = None
                    function.expiration = datetime.utcnow() + function.lifetime
                if function.cache is None:
                    function.cache = function(*args, **kwargs)
                return function.cache

            @wraps(function)
            def wrapper_without_time(*args, **kwargs):
                if function.cache is None:
                    function.cache = function(*args, **kwargs)
                return function.cache
            return wrapper_with_time if seconds > 0 else wrapper_without_time
        return decorator

    def reset_cache(self, key: str):
        """Remove key related cache"""
        if key in self.__cache_list:
            for function in self.__cache_list[key]:
                function.cache = None
