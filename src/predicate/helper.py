from .predicate_base import PredicateBase
from .equal_predicate import EqualPredicate
from .in_list_predicate import InListPredicate


def inList(*args) -> PredicateBase:
    return InListPredicate([*args])


def equal(value) -> PredicateBase:
    return EqualPredicate(value)
