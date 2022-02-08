
from typing import Any, Callable, Coroutine

from bclib.predicate import Predicate, InList, Equal, Url, Between, NotEqual, GreaterThan, LessThan, LessThanEqual, GreaterThanEqual, Match, HasValue, Callback, All
from bclib import predicate
from bclib.context import Context


class DispatcherHelper:

    @staticmethod
    def in_list(expression: str, *items) -> Predicate:
        """Create list cheking predicate"""

        return InList(expression,  *items)

    @staticmethod
    def equal(expression: str, value: Any) -> Predicate:
        """Create equality cheking predicate"""

        return Equal(expression, value)

    @staticmethod
    def url(pattern: str) -> Predicate:
        """Create url cheking predicate"""

        return Url(pattern)

    @staticmethod
    def between(expression: str, min_value: int, max_value: int) -> Predicate:
        """Create between cheking predicate"""

        return Between(expression, min_value, max_value)

    @staticmethod
    def not_equal(expression: str, value: Any) -> Predicate:
        """Create not equality cheking predicate"""

        return NotEqual(expression, value)

    @staticmethod
    def greater_than(expression: str, value: int) -> Predicate:
        """Create not greater than cheking predicate"""

        return GreaterThan(expression, value)

    @staticmethod
    def less_than(expression: str, value: int) -> Predicate:
        """Create not less than cheking predicate"""

        return LessThan(expression, value)

    @staticmethod
    def less_than_equal(expression: str, value: int) -> Predicate:
        """Create not less than and equal cheking predicate"""

        return LessThanEqual(expression, value)

    @staticmethod
    def greater_than_equal(expression: str, value: int) -> Predicate:
        """Create not less than and equal cheking predicate"""

        return GreaterThanEqual(expression, value)

    @staticmethod
    def match(expression: str, value: str) -> Predicate:
        """Create regex matching cheking predicate"""

        return Match(expression, value)

    @staticmethod
    def has_value(expression: str) -> Predicate:
        """Create has value cheking predicate"""

        return HasValue(expression)

    @staticmethod
    def callback(callback: 'Callable[[Context],Coroutine[bool]]') -> Predicate:
        """Create Callback cheking predicate"""

        return Callback(callback)

    @staticmethod
    def is_post() -> Predicate:
        """create http post request cheking predicate"""

        return Equal("context.cms.request.methode", "post")

    @staticmethod
    def is_get() -> Predicate:
        """create http get request cheking predicate"""

        return Equal("context.cms.request.methode", "get")

    @staticmethod
    def is_put() -> Predicate:
        """create http put request cheking predicate"""

        return Equal("context.cms.request.methode", "put")

    @staticmethod
    def is_delete() -> Predicate:
        """create http delete request cheking predicate"""

        return Equal("context.cms.request.methode", "delete")

    @staticmethod
    def all(*predicates: 'Predicate') -> Predicate:
        """create all cheking predicate"""

        return All(predicates)

    @staticmethod
    def any(*predicates: 'Predicate') -> Predicate:
        """create any cheking predicate"""

        return predicate.Any(predicates)

    @staticmethod
    def post(url: str) -> Predicate:
        """create http post request cheking predicate"""

        return All(DispatcherHelper.url(url), DispatcherHelper.is_post())

    @staticmethod
    def get(url: str) -> Predicate:
        """create http get request cheking predicate"""

        return All(DispatcherHelper.url(url), DispatcherHelper.is_get())

    @staticmethod
    def put(url: str) -> Predicate:
        """create http put request cheking predicate"""

        return All(DispatcherHelper.url(url), DispatcherHelper.is_put())

    @staticmethod
    def delete(url: str) -> Predicate:
        """create http delete request cheking predicate"""

        return All(DispatcherHelper.url(url), DispatcherHelper.is_delete())
