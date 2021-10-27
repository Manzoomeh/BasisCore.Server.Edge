from typing import Callable
from context import Context
from predicate import Predicate
from .callback_result import CallbackResult


class CallbackInfo:
    def __init__(self, predicates: list[Predicate],  callback: Callable[[Context], CallbackResult]) -> CallbackResult:
        self.__callback = callback
        self.__predicates = predicates

    def try_execute(self, context: Context) -> CallbackResult:
        result = None
        for predicate in self.__predicates:
            if predicate.check(context) is False:
                break
        else:
            result = self.__callback(context)
        return result
