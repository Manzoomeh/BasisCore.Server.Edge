from typing import Any, Callable, Coroutine
from ..context import Context
from ..predicate import Predicate
from bclib.exception import ShortCircuitErr


class CallbackInfo:
    def __init__(self, predicates: 'list[Predicate]',  async_callback: 'Callable[[Context], Coroutine[Any]]') -> Any:
        self.__async_callback = async_callback
        self.__predicates = predicates

    async def try_execute_async(self, context: Context) -> Any:
        result: Any = None
        for predicate in self.__predicates:
            try:
                if not (await predicate.check_async(context)):
                    break
            except ShortCircuitErr as ex:
                result = context.generate_error_response(ex)
                break
        else:
            
            result = await self.__async_callback(context)
        return result

    @property
    def callback_name(self):
        return self.__async_callback.__name__