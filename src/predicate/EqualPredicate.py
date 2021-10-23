from .IPredicate import IPredicate


class EqualPredicate (IPredicate):
    def __init__(self, value) -> None:
        self._value = value

    def isMatch(self, value) -> bool:
        return self._value == value
