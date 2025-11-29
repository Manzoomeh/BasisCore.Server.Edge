"""
All Predicate Module

Provides logical AND combinator for predicates. Returns True only if all predicates pass.

Features:
    - Combines multiple predicates with AND logic
    - Short-circuits on first False result
    - Exception-safe evaluation

Example:
    ```python
    from bclib.predicate import All, Equal, HasValue
    
    # All conditions must be true
    predicate = All(
        Equal("context.query.role", "admin"),
        HasValue("context.query.user_id")
    )
    ```
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class All(Predicate):
    """
    Logical AND predicate combinator

    Returns True only if all contained predicates evaluate to True.
    Short-circuits on the first False result for performance.

    Args:
        *predicates: Variable number of Predicate instances to combine with AND logic

    Example:
        ```python
        # Check if user is admin AND has valid session
        predicate = All(
            Equal("context.query.role", "admin"),
            HasValue("context.session.token")
        )

        # Use in decorator
        @app.handler(predicates=[All(is_admin, has_permission)])
        async def restricted_handler(context):
            pass
        ```
    """

    def __init__(self, *predicates: 'Predicate') -> None:
        """
        Initialize the AND combinator with predicates

        Args:
            *predicates: Variable number of Predicate instances to combine

        Note:
            Empty predicate list will always return True.
        """
        super().__init__(None)
        self.__predicate_list = predicates

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if all predicates pass

        Args:
            context: Current request context to evaluate

        Returns:
            True if all predicates return True, False if any returns False

        Raises:
            Does not raise exceptions; returns False on any error

        Note:
            Short-circuits on first False result for performance.
        """
        try:
            for predicate in self.__predicate_list:
                if not await predicate.check_async(context):
                    return False
            return True
        except Exception:
            return False
