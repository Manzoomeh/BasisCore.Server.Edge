from bclib.predicate.predicate import Predicate
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bclib.context.context import Context


class InList(Predicate):
    """Create list checking predicate"""

    def __init__(self, expression: str, *items: Any) -> None:
        super().__init__(expression)
        self.__items = [*items]

    async def check_async(self, context: 'Context') -> 'bool':
        try:
            value = eval(self.expression, {}, {"context": context})
            return value in self.__items
        except:  # pylint: disable=bare-except
            return False
