from bclib.context import Context
from ..predicate.predicate import Predicate


class Equal (Predicate):
    """Create equality cheking predicate"""

    def __init__(self, expression, value) -> None:
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: Context) -> bool:
        try:
            value = eval(self.exprossion, {}, {"context": context})
            return self.__value == value
        except:  # pylint: disable=bare-except
            return False
