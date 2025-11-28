"""
Any Predicate Module

Provides logical OR combinator for predicates. Returns True if at least one predicate passes.

Features:
    - Combines multiple predicates with OR logic
    - Short-circuits on first True result
    - Exception-safe evaluation

Example:
    ```python
    from bclib.predicate import Any, Equal
    
    # Match if user is admin OR moderator
    predicate = Any(
        Equal("context.query.role", "admin"),
        Equal("context.query.role", "moderator")
    )
    ```
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class Any(Predicate):
    """
    Logical OR predicate combinator

    Returns True if at least one of the contained predicates evaluates to True.
    Short-circuits on the first True result for performance.

    Args:
        *predicates: Variable number of Predicate instances to combine with OR logic

    Example:
        ```python
        # Match if method is GET OR POST
        method_check = Any(is_get(), is_post())

        # Match if user is admin OR moderator
        role_check = Any(
            Equal("context.query.role", "admin"),
            Equal("context.query.role", "moderator")
        )

        @app.action(predicates=[Any(is_admin, is_moderator)])
        async def privileged_handler(context):
            pass
        ```
    """

    def __init__(self, *predicates: 'Predicate') -> None:
        """
        Initialize OR combinator with predicates

        Args:
            *predicates: Variable number of predicates to combine

        Note:
            Empty predicate list will always return False.
        """
        super().__init__(None)
        self.__predicate_list = predicates

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if at least one predicate passes

        Args:
            context: Current request context to evaluate

        Returns:
            True if any predicate returns True, False if all return False

        Raises:
            Does not raise exceptions; returns False on any error

        Note:
            Short-circuits on first True result for performance.
        """
        try:
            for predicate in self.__predicate_list:
                if await predicate.check_async(context):
                    return True
            return False
        except Exception:
            return False
        super().__init__(None)
        self.__predicate_list = predicates

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if any predicate returns True

        Args:
            context: Current request context

        Returns:
            True if at least one predicate is True, False otherwise
        """
        try:
            for predicate in self.__predicate_list:
                if await predicate.check_async(context):
                    return True
            return False
        except Exception as ex:
            print("Error in any predicate", ex)
            return False
