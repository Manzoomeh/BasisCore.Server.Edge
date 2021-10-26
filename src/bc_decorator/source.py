from typing import Callable
from .callback_info import CallbackInfo
from context import SourceContext
from predicate.predicate import Predicate
from .callback_result import CallbackResult
from .dispatcher import get_lookup


class SourceCallbackInfo(CallbackInfo):
    def __init__(self, predicates: list[Predicate], callback: Callable[[SourceContext], CallbackResult]) -> CallbackResult:
        super().__init__(predicates, callback)


def sourceAction(*predicates):
    def decorator(function):
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            return result
        get_lookup(SourceContext.__name__).append(
            SourceCallbackInfo([*predicates], wrapper))
        return wrapper
    return decorator
