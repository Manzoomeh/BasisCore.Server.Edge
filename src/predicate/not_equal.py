from context import Context
from .predicate import Predicate
from typing import Any


class NotEqual (Predicate):
    """Create not equality cheking predicate"""

    def __init__(self, expression: str, value: Any) -> None:
        super().__init__(expression)
        self.__value = value

    def check(self, context: Context) -> bool:
        try:
            value = eval(self.exprossion, {}, {"context": context})
            return self.__value != value
        except:
            return False
