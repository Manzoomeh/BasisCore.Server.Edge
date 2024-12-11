from bclib.predicate.predicate import Predicate
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bclib.context.context import Context


class NotEqual (Predicate):
    """Create not equality checking predicate"""

    def __init__(self, expression: str, value: Any) -> None:
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: 'Context') -> 'bool':
        try:
            value = eval(self.expression, {}, {"context": context})
            return self.__value != value
        except:  # pylint: disable=bare-except
            return False
