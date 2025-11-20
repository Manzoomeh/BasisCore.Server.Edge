from bclib.context import Context

from ..predicate.predicate import Predicate


class All (Predicate):
    """Create all predicate list cheking predicate"""

    def __init__(self, *predicate: 'Predicate') -> None:
        super().__init__(None)
        self.__predicate_list = predicate

    async def check_async(self, context: Context) -> bool:
        is_ok = True
        try:
            for predicate in self.__predicate_list:
                if not await predicate.check_async(context):
                    is_ok = False
                    break
        except:  # pylint: disable=bare-except
            is_ok = False
        return is_ok
