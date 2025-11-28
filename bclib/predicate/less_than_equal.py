from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context
    
from ..predicate.predicate import Predicate


class LessThanEqual (Predicate):
    """Create less than and equal cheking predicate"""

    def __init__(self, expression: str, value: int) -> None:
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: 'Context') -> bool:
        try:
            value = eval(self.exprossion, {}, {"context": context})
            return self.__value >= value
        except:  # pylint: disable=bare-except
            return False
