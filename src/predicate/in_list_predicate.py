from .predicate_base import PredicateBase


class InListPredicate(PredicateBase):
    def __init__(self, args: list) -> None:
        self._list = args

    def isMatch(self, value) -> bool:
        return value in self._list
