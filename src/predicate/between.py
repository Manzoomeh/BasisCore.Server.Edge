from context import Context
from .predicate import Predicate


class Between(Predicate):
    """Create between cheking predicate"""

    def __init__(self, expression: str, min_value: int, max_value: int):
        super().__init__(expression)
        self.__min_value = min_value
        self.__max_value = max_value

    def check(self, context: Context) -> bool:
        try:
            value = eval(self.exprossion, {}, {"context": context})
            return self.__min_value < int(value) < self.__max_value
        except:
            return False
