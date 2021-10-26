from .predicate_base import PredicateBase


class EqualPredicate (PredicateBase):
    def __init__(self, value) -> None:
        self._value = value

    def isMatch(self, value) -> bool:
        return self._value == value
