from typing import TYPE_CHECKING
from bclib.exception import ShortCircuitErr

if TYPE_CHECKING:
    from typing import Any, Callable, Awaitable
    from bclib.predicate import Predicate
    from bclib.context.context import Context


class CallbackInfo:
    def __init__(self, predicates: 'list[Predicate]',  async_callback: 'Callable[[Context], Awaitable[Any]]') -> 'Any':
        self.__async_callback = async_callback
        self.__predicates = predicates

    async def try_execute_async(self, context: 'Context') -> 'Any':
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
