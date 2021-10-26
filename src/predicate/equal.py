from context import Context
from .predicate import Predicate


class Equal (Predicate):
    """Create equality cheking predicate"""

    def __init__(self, expression, value) -> None:
        super().__init__(expression)
        self.__value = value

    def check(self, context: Context) -> bool:
        value = eval(self.exprossion, {}, {"context": context})
        return self.__value == value
