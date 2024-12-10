from bclib.predicate.predicate import Predicate
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bclib.context.context import Context


class Between(Predicate):
    """Create between cheking predicate"""

    def __init__(self, expression: str, min_value: int, max_value: int):
        super().__init__(expression)
        self.__min_value = min_value
        self.__max_value = max_value

    async def check_async(self, context: 'Context') -> 'bool':
        try:
            value = eval(self.expression, {}, {"context": context})
            return self.__min_value < int(value) < self.__max_value
        except:  # pylint: disable=bare-except
            return False
