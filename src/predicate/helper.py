from src.predicate.IPredicate import IPredicate
from src.predicate.InListPredicate import InListPredicate
from src.predicate.EqualPredicate import EqualPredicate


def inList(*args) -> IPredicate:
    return InListPredicate([*args])


def equal(value) -> IPredicate:
    return EqualPredicate(value)
