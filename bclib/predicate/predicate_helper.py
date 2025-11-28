from typing import TYPE_CHECKING, Any, Callable, Coroutine

if TYPE_CHECKING:
    from bclib.context import Context
    from bclib.predicate.predicate import Predicate


class PredicateHelper:
    """
    Helper class providing predicate factory methods for request filtering and routing.

    This class contains static methods that create various predicate objects used
    for handler registration and request matching in the Dispatcher.
    """

    @staticmethod
    def in_list(expression: str, *items) -> 'Predicate':
        """Create list checking predicate"""
        from bclib.predicate.in_list import InList
        return InList(expression, *items)

    @staticmethod
    def equal(expression: str, value: Any) -> 'Predicate':
        """Create equality checking predicate"""
        from bclib.predicate.equal import Equal
        return Equal(expression, value)

    @staticmethod
    def url(pattern: str) -> 'Predicate':
        """Create URL checking predicate"""
        from bclib.predicate.url import Url
        return Url(pattern)

    @staticmethod
    def between(expression: str, min_value: int, max_value: int) -> 'Predicate':
        """Create between checking predicate"""
        from bclib.predicate.between import Between
        return Between(expression, min_value, max_value)

    @staticmethod
    def not_equal(expression: str, value: Any) -> 'Predicate':
        """Create not equality checking predicate"""
        from bclib.predicate.not_equal import NotEqual
        return NotEqual(expression, value)

    @staticmethod
    def greater_than(expression: str, value: int) -> 'Predicate':
        """Create greater than checking predicate"""
        from bclib.predicate.greater_than import GreaterThan
        return GreaterThan(expression, value)

    @staticmethod
    def less_than(expression: str, value: int) -> 'Predicate':
        """Create less than checking predicate"""
        from bclib.predicate.less_than import LessThan
        return LessThan(expression, value)

    @staticmethod
    def less_than_equal(expression: str, value: int) -> 'Predicate':
        """Create less than and equal checking predicate"""
        from bclib.predicate.less_than_equal import LessThanEqual
        return LessThanEqual(expression, value)

    @staticmethod
    def greater_than_equal(expression: str, value: int) -> 'Predicate':
        """Create greater than and equal checking predicate"""
        from bclib.predicate.greater_than_equal import GreaterThanEqual
        return GreaterThanEqual(expression, value)

    @staticmethod
    def match(expression: str, value: str) -> 'Predicate':
        """Create regex matching checking predicate"""
        from bclib.predicate.match import Match
        return Match(expression, value)

    @staticmethod
    def has_value(expression: str) -> 'Predicate':
        """Create has value checking predicate"""
        from bclib.predicate.has_value import HasValue
        return HasValue(expression)

    @staticmethod
    def callback(callback: 'Callable[[Context], Coroutine[bool]]') -> 'Predicate':
        """Create callback checking predicate"""
        from bclib.predicate.callback import Callback
        return Callback(callback)

    @staticmethod
    def is_post() -> 'Predicate':
        """Create HTTP POST request checking predicate"""
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "post")

    @staticmethod
    def is_get() -> 'Predicate':
        """Create HTTP GET request checking predicate"""
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "get")

    @staticmethod
    def is_put() -> 'Predicate':
        """Create HTTP PUT request checking predicate"""
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "put")

    @staticmethod
    def is_delete() -> 'Predicate':
        """Create HTTP DELETE request checking predicate"""
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "delete")

    @staticmethod
    def is_options() -> 'Predicate':
        """Create HTTP OPTIONS request checking predicate"""
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "options")

    @staticmethod
    def all(*predicates: 'Predicate') -> 'Predicate':
        """Create all checking predicate (logical AND)"""
        from bclib.predicate.all import All
        return All(predicates)

    @staticmethod
    def any(*predicates: 'Predicate') -> 'Predicate':
        """Create any checking predicate (logical OR)"""
        from bclib.predicate.any import Any
        return Any(predicates)

    @staticmethod
    def post(url: str) -> 'Predicate':
        """Create HTTP POST request checking predicate with URL"""
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_post())

    @staticmethod
    def get(url: str) -> 'Predicate':
        """Create HTTP GET request checking predicate with URL"""
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_get())

    @staticmethod
    def put(url: str) -> 'Predicate':
        """Create HTTP PUT request checking predicate with URL"""
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_put())

    @staticmethod
    def delete(url: str) -> 'Predicate':
        """Create HTTP DELETE request checking predicate with URL"""
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_delete())

    @staticmethod
    def options(url: str) -> 'Predicate':
        """Create HTTP OPTIONS request checking predicate with URL"""
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_options())

    @staticmethod
    def build_predicates(
        route: str = None,
        method: 'str | list[str]' = None,
        *predicates: 'Predicate'
    ) -> 'list[Predicate]':
        """
        Build a combined list of predicates from decorator parameters

        This helper method consolidates the logic for building predicates from
        route, method(s), and additional predicates. It's used by web_action and 
        restful_action decorators to simplify their implementation.

        Args:
            route: Optional URL route pattern as first argument (e.g., "users/:id", "api/posts")
            method: Optional HTTP method filter - single string ("get") or list (["GET", "POST"])
            *predicates: Variable number of additional Predicate objects

        Returns:
            Combined list of all predicates

        Example:
            ```python
            # Simple usage with route and single method
            predicates = PredicateHelper.build_predicates("users/:id", method="GET")
            # Returns: [Url("users/:id"), is_get()]

            # Multiple methods as array - each added separately
            predicates = PredicateHelper.build_predicates("api/posts", method=["GET", "POST"])
            # Returns: [Url("api/posts"), is_get(), is_post()]

            # With additional predicates
            predicates = PredicateHelper.build_predicates(
                "admin",
                method="GET",
                PredicateHelper.has_value("context.query.token")
            )
            # Returns: [Url("admin"), is_get(), HasValue("context.query.token")]

            # No route, just predicates
            predicates = PredicateHelper.build_predicates(
                None,
                None,
                PredicateHelper.equal("context.query.type", "admin")
            )
            # Returns: [Equal("context.query.type", "admin")]
            ```
        """
        combined_predicates = list(predicates)

        # Normalize method to list
        methods_list = []
        if method is not None:
            if isinstance(method, str):
                methods_list = [method]
            else:
                methods_list = method

        # Add URL predicate if route is provided
        if route is not None:
            combined_predicates.append(PredicateHelper.url(route))

        # Add method predicates separately
        if len(methods_list) > 0:
            for m in methods_list:
                method_lower = m.lower()
                if method_lower == "post":
                    combined_predicates.append(PredicateHelper.is_post())
                elif method_lower == "get":
                    combined_predicates.append(PredicateHelper.is_get())
                elif method_lower == "put":
                    combined_predicates.append(PredicateHelper.is_put())
                elif method_lower == "delete":
                    combined_predicates.append(PredicateHelper.is_delete())
                elif method_lower == "options":
                    combined_predicates.append(PredicateHelper.is_options())

        return combined_predicates
