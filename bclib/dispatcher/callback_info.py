from typing import Any, Callable
from ..context import Context
from ..predicate import Predicate
from bclib.exception import ShortCircuitErr


class CallbackInfo:
    def __init__(self, predicates: 'list[Predicate]',  callback: 'Callable[[Context], Any]') -> Any:
        self.__callback = callback
        self.__predicates = predicates

    def try_execute(self, context: Context) -> Any:
        result: Any = None
        for predicate in self.__predicates:
            try:
                if predicate.check(context) is False:
                    break
            except ShortCircuitErr as ex:
                result = context.generate_error_responce(ex)
                break
        else:
            result = self.__callback(context)
        return result
