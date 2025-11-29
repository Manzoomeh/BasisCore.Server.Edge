"""
Predicate Helper Module

Provides factory methods and utilities for creating and combining predicates.
This module centralizes predicate creation logic used throughout the framework.

Features:
    - Factory methods for all predicate types
    - HTTP method predicates (GET, POST, PUT, DELETE, OPTIONS)
    - Logical combinators (AND, OR)
    - Convenient route + method builders
    - build_predicates() for decorator parameter consolidation

Example:
    ```python
    from bclib.predicate import PredicateHelper
    
    # Create individual predicates
    user_check = PredicateHelper.equal("context.query.user_id", "123")
    admin_check = PredicateHelper.in_list("context.query.role", "admin", "moderator")
    
    # Combine predicates
    predicates = PredicateHelper.build_predicates(
        route="/api/users/:id",
        method="GET",
        PredicateHelper.has_value("context.query.token")
    )
    ```
"""

from typing import TYPE_CHECKING, Any, Callable, Coroutine

if TYPE_CHECKING:
    from bclib.context import Context
    from bclib.predicate.predicate import Predicate


class PredicateHelper:
    """
    Factory class for creating and combining predicates

    Provides static methods to create predicate instances and combine them
    for use in handler registration and request routing.

    Note:
        All methods use lazy imports to avoid circular dependencies.

    Example:
        ```python
        # Create comparison predicates
        age_check = PredicateHelper.greater_than("context.query.age", 18)
        status_check = PredicateHelper.equal("context.query.status", "active")

        # Create HTTP method predicates
        get_predicate = PredicateHelper.is_get()
        post_predicate = PredicateHelper.is_post()

        # Combine with logical operators
        combined = PredicateHelper.all(age_check, status_check)
        either = PredicateHelper.any(get_predicate, post_predicate)
        ```
    """

    @staticmethod
    def in_list(expression: str, *items: Any) -> 'Predicate':
        """
        Create list membership predicate

        Args:
            expression: Path to value in context
            *items: Allowed values to check against

        Returns:
            InList predicate instance

        Example:
            ```python
            # Check if role is admin or moderator
            role_check = PredicateHelper.in_list(
                "context.query.role", "admin", "moderator"
            )
            ```
        """
        from bclib.predicate.in_list import InList
        return InList(expression, *items)

    @staticmethod
    def equal(expression: str, value: Any) -> 'Predicate':
        """
        Create equality predicate

        Args:
            expression: Path to value in context
            value: Expected value to match

        Returns:
            Equal predicate instance

        Example:
            ```python
            status_check = PredicateHelper.equal(
                "context.query.status", "active"
            )
            ```
        """
        from bclib.predicate.equal import Equal
        return Equal(expression, value)

    @staticmethod
    def url(pattern: str) -> 'Predicate':
        """
        Create URL pattern matching predicate

        Args:
            pattern: URL pattern with optional parameters (e.g., "/users/:id")

        Returns:
            Url predicate instance

        Example:
            ```python
            # Static URL
            home = PredicateHelper.url("/")

            # URL with parameter
            user_detail = PredicateHelper.url("/users/:id")

            # Wildcard parameter
            files = PredicateHelper.url("/files/:*path")
            ```
        """
        from bclib.predicate.url import Url
        return Url(pattern)

    @staticmethod
    def between(expression: str, min_value: int, max_value: int) -> 'Predicate':
        """
        Create range checking predicate (exclusive bounds)

        Args:
            expression: Path to numeric value in context
            min_value: Minimum bound (exclusive)
            max_value: Maximum bound (exclusive)

        Returns:
            Between predicate instance

        Example:
            ```python
            age_range = PredicateHelper.between(
                "context.query.age", 18, 65
            )
            ```
        """
        from bclib.predicate.between import Between
        return Between(expression, min_value, max_value)

    @staticmethod
    def not_equal(expression: str, value: Any) -> 'Predicate':
        """
        Create inequality predicate

        Args:
            expression: Path to value in context
            value: Value that should NOT match

        Returns:
            NotEqual predicate instance

        Example:
            ```python
            not_deleted = PredicateHelper.not_equal(
                "context.query.status", "deleted"
            )
            ```
        """
        from bclib.predicate.not_equal import NotEqual
        return NotEqual(expression, value)

    @staticmethod
    def greater_than(expression: str, value: int) -> 'Predicate':
        """
        Create greater than predicate

        Args:
            expression: Path to numeric value
            value: Threshold (exclusive)

        Returns:
            GreaterThan predicate instance
        """
        from bclib.predicate.greater_than import GreaterThan
        return GreaterThan(expression, value)

    @staticmethod
    def less_than(expression: str, value: int) -> 'Predicate':
        """
        Create less than predicate

        Args:
            expression: Path to numeric value
            value: Threshold (exclusive)

        Returns:
            LessThan predicate instance
        """
        from bclib.predicate.less_than import LessThan
        return LessThan(expression, value)

    @staticmethod
    def less_than_equal(expression: str, value: int) -> 'Predicate':
        """
        Create less than or equal predicate

        Args:
            expression: Path to numeric value
            value: Maximum threshold (inclusive)

        Returns:
            LessThanEqual predicate instance
        """
        from bclib.predicate.less_than_equal import LessThanEqual
        return LessThanEqual(expression, value)

    @staticmethod
    def greater_than_equal(expression: str, value: int) -> 'Predicate':
        """
        Create greater than or equal predicate

        Args:
            expression: Path to numeric value
            value: Minimum threshold (inclusive)

        Returns:
            GreaterThanEqual predicate instance
        """
        from bclib.predicate.greater_than_equal import GreaterThanEqual
        return GreaterThanEqual(expression, value)

    @staticmethod
    def match(expression: str, pattern: str) -> 'Predicate':
        """
        Create regex matching predicate

        Args:
            expression: Path to string value
            pattern: Regular expression pattern

        Returns:
            Match predicate instance

        Example:
            ```python
            email_check = PredicateHelper.match(
                "context.query.email",
                r"^[\\w.-]+@[\\w.-]+\\.\\w+$"
            )
            ```
        """
        from bclib.predicate.match import Match
        return Match(expression, pattern)

    @staticmethod
    def has_value(expression: str) -> 'Predicate':
        """
        Create value existence predicate

        Args:
            expression: Path to value to check

        Returns:
            HasValue predicate instance

        Example:
            ```python
            has_token = PredicateHelper.has_value(
                "context.query.api_key"
            )
            ```
        """
        from bclib.predicate.has_value import HasValue
        return HasValue(expression)

    @staticmethod
    def callback(callback: 'Callable[[Context], Coroutine[bool]]') -> 'Predicate':
        """
        Create custom callback predicate

        Args:
            callback: Async function taking Context and returning bool

        Returns:
            Callback predicate instance

        Example:
            ```python
            async def custom_check(context):
                user = await get_user(context.query.user_id)
                return user.is_premium

            premium_check = PredicateHelper.callback(custom_check)
            ```
        """
        from bclib.predicate.callback import Callback
        return Callback(callback)

    @staticmethod
    def is_post() -> 'Predicate':
        """
        Create HTTP POST method predicate

        Returns:
            Predicate checking for POST requests
        """
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "post")

    @staticmethod
    def is_get() -> 'Predicate':
        """
        Create HTTP GET method predicate

        Returns:
            Predicate checking for GET requests
        """
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "get")

    @staticmethod
    def is_put() -> 'Predicate':
        """
        Create HTTP PUT method predicate

        Returns:
            Predicate checking for PUT requests
        """
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "put")

    @staticmethod
    def is_delete() -> 'Predicate':
        """
        Create HTTP DELETE method predicate

        Returns:
            Predicate checking for DELETE requests
        """
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "delete")

    @staticmethod
    def is_options() -> 'Predicate':
        """
        Create HTTP OPTIONS method predicate

        Returns:
            Predicate checking for OPTIONS requests
        """
        from bclib.predicate.equal import Equal
        return Equal("context.cms.request.methode", "options")

    @staticmethod
    def all(*predicates: 'Predicate') -> 'Predicate':
        """
        Create logical AND combinator

        Args:
            *predicates: Predicates to combine with AND logic

        Returns:
            All predicate (returns True only if all predicates pass)

        Example:
            ```python
            # Both conditions must be true
            combined = PredicateHelper.all(
                PredicateHelper.is_get(),
                PredicateHelper.has_value("context.query.token")
            )
            ```
        """
        from bclib.predicate.all import All
        return All(*predicates)

    @staticmethod
    def any(*predicates: 'Predicate') -> 'Predicate':
        """
        Create logical OR combinator

        Args:
            *predicates: Predicates to combine with OR logic

        Returns:
            Any predicate (returns True if at least one predicate passes)

        Example:
            ```python
            # Either condition can be true
            combined = PredicateHelper.any(
                PredicateHelper.is_get(),
                PredicateHelper.is_post()
            )
            ```
        """
        from bclib.predicate.any import Any
        return Any(*predicates)

    @staticmethod
    def post(url: str) -> 'Predicate':
        """
        Create POST request with URL predicate

        Args:
            url: URL pattern to match

        Returns:
            Combined predicate for POST method and URL

        Example:
            ```python
            create_user = PredicateHelper.post("/api/users")
            ```
        """
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_post())

    @staticmethod
    def get(url: str) -> 'Predicate':
        """
        Create GET request with URL predicate

        Args:
            url: URL pattern to match

        Returns:
            Combined predicate for GET method and URL

        Example:
            ```python
            get_user = PredicateHelper.get("/api/users/:id")
            ```
        """
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_get())

    @staticmethod
    def put(url: str) -> 'Predicate':
        """
        Create PUT request with URL predicate

        Args:
            url: URL pattern to match

        Returns:
            Combined predicate for PUT method and URL
        """
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_put())

    @staticmethod
    def delete(url: str) -> 'Predicate':
        """
        Create DELETE request with URL predicate

        Args:
            url: URL pattern to match

        Returns:
            Combined predicate for DELETE method and URL
        """
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_delete())

    @staticmethod
    def options(url: str) -> 'Predicate':
        """
        Create OPTIONS request with URL predicate

        Args:
            url: URL pattern to match

        Returns:
            Combined predicate for OPTIONS method and URL
        """
        from bclib.predicate.all import All
        return All(PredicateHelper.url(url), PredicateHelper.is_options())

    @staticmethod
    def build_predicates(
        route: str = None,
        method: 'str | list[str]' = None,
        *predicates: 'Predicate'
    ) -> 'list[Predicate]':
        """
        Build combined list of predicates from decorator parameters

        Consolidates logic for building predicates from route, method(s), and
        additional predicates. Used internally by handler decorators.

        Args:
            route: Optional URL route pattern (e.g., "users/:id", "api/posts")
            method: Optional HTTP method filter - single string ("get") or list (["GET", "POST"])
                   Supports standard methods (GET, POST, PUT, DELETE, OPTIONS) and custom methods
            *predicates: Additional Predicate objects to include

        Returns:
            Combined list of all predicates

        Note:
            - If route is provided, adds Url predicate
            - If single method, adds corresponding method predicate
            - If multiple methods, wraps in Any predicate (logical OR)
            - Standard methods (GET, POST, PUT, DELETE, OPTIONS) use optimized predicates
            - Custom/unknown methods are handled via inline Equal predicate
            - Additional predicates are appended as-is

        Example:
            ```python
            # Simple usage with route and single method
            predicates = PredicateHelper.build_predicates("users/:id", "GET")
            # Returns: [Url("users/:id"), is_get()]

            # Multiple methods - wrapped in Any predicate
            predicates = PredicateHelper.build_predicates(
                "api/posts", 
                ["GET", "POST"]
            )
            # Returns: [Url("api/posts"), Any(is_get(), is_post())]

            # Custom HTTP method (e.g., PATCH)
            predicates = PredicateHelper.build_predicates(
                "api/resource/:id",
                "PATCH"
            )
            # Returns: [Url("api/resource/:id"), Equal("context.cms.request.methode", "patch")]

            # With additional predicates
            predicates = PredicateHelper.build_predicates(
                "admin",
                "GET",
                PredicateHelper.has_value("context.query.token")
            )
            # Returns: [
            #     Url("admin"), 
            #     is_get(), 
            #     HasValue("context.query.token")
            # ]

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

        # Add URL predicate if route is provided
        if route is not None:
            combined_predicates.append(PredicateHelper.url(route))

        # Normalize method to list
        methods_list = []
        if method is not None:
            if isinstance(method, str):
                methods_list = [method]
            else:
                methods_list = method

        # Add method predicates - use Any if multiple methods
        if len(methods_list) > 0:
            method_predicates: list['Predicate'] = []
            for m in methods_list:
                method_lower = m.lower()
                if method_lower == "post":
                    method_predicates.append(PredicateHelper.is_post())
                elif method_lower == "get":
                    method_predicates.append(PredicateHelper.is_get())
                elif method_lower == "put":
                    method_predicates.append(PredicateHelper.is_put())
                elif method_lower == "delete":
                    method_predicates.append(PredicateHelper.is_delete())
                elif method_lower == "options":
                    method_predicates.append(PredicateHelper.is_options())
                else:
                    # Unknown method - create inline equal predicate
                    from bclib.predicate.equal import Equal
                    method_predicates.append(
                        Equal("context.cms.request.methode", method_lower))

            # If multiple methods, wrap in Any predicate
            if len(method_predicates) == 1:
                combined_predicates.append(method_predicates[0])
            elif len(method_predicates) > 1:
                combined_predicates.append(
                    PredicateHelper.any(*method_predicates))

        return combined_predicates
