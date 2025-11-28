import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context
    
from ..predicate.predicate import Predicate


class Match (Predicate):
    """Create regex matching cheking predicate"""

    def __init__(self, expression: str, value: str) -> None:
        super().__init__(expression)
        self.__compiled_regex = re.compile(value)

    async def check_async(self, context: 'Context') -> bool:
        try:
            value = eval(self.exprossion, {}, {"context": context})
            return self.__compiled_regex.match(str(value)) != None
        except:  # pylint: disable=bare-except
            return False
