from ..predicate.predicate import Predicate
from typing import Callable
from bclib.context import Context


class Callback (Predicate):
    """Create callback base cheking predicate"""

    def __init__(self, callback: 'Callable[[Context],bool]') -> None:
        super().__init__(None)
        self.__callback = callback

    def check(self, context: Context) -> bool:
        try:
            return self.__callback(context)
        except:  # pylint: disable=bare-except
            return False
