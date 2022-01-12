from typing import Any
from bclib.context import Context
from ..predicate.predicate import Predicate


class InList(Predicate):
    """Create list cheking predicate"""

    def __init__(self, expression: str, *items: Any) -> None:
        super().__init__(expression)
        self.__items = [*items]

    def check(self, context: Context) -> bool:
        try:
            value = eval(self.exprossion, {}, {"context": context})
            return value in self.__items
        except:  # pylint: disable=bare-except
            return False
