from .IPredicate import IPredicate


class InListPredicate(IPredicate):
    def __init__(self, args: list) -> None:
        self._list = args

    def isMatch(self, value) -> bool:
        return value in self._list
