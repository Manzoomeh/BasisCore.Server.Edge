from bclib.exception import ShortCircuitErr
from ..predicate.predicate import Predicate
from typing import Callable, Coroutine
from bclib.context import Context


class Callback (Predicate):
    """Create callback base cheking predicate"""

    def __init__(self, callback: 'Callable[[Context],Coroutine[bool]]') -> None:
        super().__init__(None)
        self.__callback = callback

    async def check_async(self, context: Context) -> bool:
        try:
            return await self.__callback(context)
        except ShortCircuitErr:
            raise
        except:  # pylint: disable=bare-except
            return False
