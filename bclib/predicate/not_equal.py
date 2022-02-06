from bclib.context import Context
from ..predicate.predicate import Predicate
from typing import Any


class NotEqual (Predicate):
    """Create not equality cheking predicate"""

    def __init__(self, expression: str, value: Any) -> None:
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: Context) -> bool:
        try:
            value = eval(self.exprossion, {}, {"context": context})
            return self.__value != value
        except:  # pylint: disable=bare-except
            return False
