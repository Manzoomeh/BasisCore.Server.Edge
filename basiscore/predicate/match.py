import re
from ..context import Context
from ..predicate.predicate import Predicate


class Match (Predicate):
    """Create regex matching cheking predicate"""

    def __init__(self, expression: str, value: str) -> None:
        super().__init__(expression)
        self.__value = value

    def check(self, context: Context) -> bool:
        try:
            value = eval(self.exprossion, {}, {"context": context})
            return re.search(self.__value, str(value)) != None
        except:  # pylint: disable=bare-except
            return False
