from ..predicate.predicate import Predicate
from bclib.context import Context


class Any (Predicate):
    """Create any predicate list cheking predicate"""

    def __init__(self, *predicate: 'Predicate') -> None:
        super().__init__(None)
        self.__predicate_list = predicate

    async def check_async(self, context: Context) -> bool:
        is_ok = False
        try:
            for predicate in self.__predicate_list:
                if await predicate.check_async(context):
                    is_ok = True
                    break
        except:  # pylint: disable=bare-except
            is_ok = False
        return is_ok
