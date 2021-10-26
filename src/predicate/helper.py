from .predicate import Predicate
from .equal import Equal
from .in_list import InList


def in_list(expression: str, *items) -> Predicate:
    """Create list cheking predicate"""
    return InList(expression,  *items)


def equal(expression: str, value) -> Predicate:
    """Create equality cheking predicate"""
    return Equal(expression, value)
