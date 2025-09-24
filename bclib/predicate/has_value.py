from bclib.predicate.predicate import Predicate
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context.context import Context


class HasValue (Predicate):
    """Create has value checking predicate"""

    def __init__(self, expression: str) -> None:
        super().__init__(expression)

    async def check_async(self, context: 'Context') -> 'bool':
        try:
            value = eval(self.expression, {}, {"context": context})
            return False if not value or value.isspace() else True
        except:  # pylint: disable=bare-except
            return False
