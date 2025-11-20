
from typing import Any, Callable, Coroutine

from bclib import predicate
from bclib.context import Context
from bclib.predicate import (All, Between, Callback, Equal, GreaterThan,
                             GreaterThanEqual, HasValue, InList, LessThan,
                             LessThanEqual, Match, NotEqual, Predicate, Url)


class DispatcherHelper:
    """
    Helper class providing predicate factory methods for request filtering and routing.

    This class contains static methods that create various predicate objects used
    for handler registration and request matching in the Dispatcher.
    """

    @staticmethod
    def in_list(expression: str, *items) -> Predicate:
        """Create list checking predicate"""
        return InList(expression, *items)

    @staticmethod
    def equal(expression: str, value: Any) -> Predicate:
        """Create equality checking predicate"""
        return Equal(expression, value)

    @staticmethod
    def url(pattern: str) -> Predicate:
        """Create URL checking predicate"""
        return Url(pattern)

    @staticmethod
    def between(expression: str, min_value: int, max_value: int) -> Predicate:
        """Create between checking predicate"""
        return Between(expression, min_value, max_value)

    @staticmethod
    def not_equal(expression: str, value: Any) -> Predicate:
        """Create not equality checking predicate"""
        return NotEqual(expression, value)

    @staticmethod
    def greater_than(expression: str, value: int) -> Predicate:
        """Create greater than checking predicate"""
        return GreaterThan(expression, value)

    @staticmethod
    def less_than(expression: str, value: int) -> Predicate:
        """Create less than checking predicate"""
        return LessThan(expression, value)

    @staticmethod
    def less_than_equal(expression: str, value: int) -> Predicate:
        """Create less than and equal checking predicate"""
        return LessThanEqual(expression, value)

    @staticmethod
    def greater_than_equal(expression: str, value: int) -> Predicate:
        """Create greater than and equal checking predicate"""
        return GreaterThanEqual(expression, value)

    @staticmethod
    def match(expression: str, value: str) -> Predicate:
        """Create regex matching checking predicate"""
        return Match(expression, value)

    @staticmethod
    def has_value(expression: str) -> Predicate:
        """Create has value checking predicate"""
        return HasValue(expression)

    @staticmethod
    def callback(callback: 'Callable[[Context], Coroutine[bool]]') -> Predicate:
        """Create callback checking predicate"""
        return Callback(callback)

    @staticmethod
    def is_post() -> Predicate:
        """Create HTTP POST request checking predicate"""
        return Equal("context.cms.request.methode", "post")

    @staticmethod
    def is_get() -> Predicate:
        """Create HTTP GET request checking predicate"""
        return Equal("context.cms.request.methode", "get")

    @staticmethod
    def is_put() -> Predicate:
        """Create HTTP PUT request checking predicate"""
        return Equal("context.cms.request.methode", "put")

    @staticmethod
    def is_delete() -> Predicate:
        """Create HTTP DELETE request checking predicate"""
        return Equal("context.cms.request.methode", "delete")

    @staticmethod
    def is_options() -> Predicate:
        """Create HTTP OPTIONS request checking predicate"""
        return Equal("context.cms.request.methode", "options")

    @staticmethod
    def all(*predicates: 'Predicate') -> Predicate:
        """Create all checking predicate (logical AND)"""
        return All(predicates)

    @staticmethod
    def any(*predicates: 'Predicate') -> Predicate:
        """Create any checking predicate (logical OR)"""
        return predicate.Any(predicates)

    @staticmethod
    def post(url: str) -> Predicate:
        """Create HTTP POST request checking predicate with URL"""
        return All([DispatcherHelper.url(url), DispatcherHelper.is_post()])

    @staticmethod
    def get(url: str) -> Predicate:
        """Create HTTP GET request checking predicate with URL"""
        return All([DispatcherHelper.url(url), DispatcherHelper.is_get()])

    @staticmethod
    def put(url: str) -> Predicate:
        """Create HTTP PUT request checking predicate with URL"""
        return All([DispatcherHelper.url(url), DispatcherHelper.is_put()])

    @staticmethod
    def delete(url: str) -> Predicate:
        """Create HTTP DELETE request checking predicate with URL"""
        return All([DispatcherHelper.url(url), DispatcherHelper.is_delete()])

    @staticmethod
    def options(url: str) -> Predicate:
        """Create HTTP OPTIONS request checking predicate with URL"""
        return All([DispatcherHelper.url(url), DispatcherHelper.is_options()])
