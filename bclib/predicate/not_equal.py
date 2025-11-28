"""
NotEqual Predicate Module

Provides inequality checking predicate for comparing context values.

Features:
    - Safe attribute and dictionary navigation
    - Support for nested paths
    - Type-safe comparison
    - Graceful error handling

Example:
    ```python
    from bclib.predicate import NotEqual
    
    # Check if status is not 'deleted'
    predicate = NotEqual("context.query.status", "deleted")
    ```
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class NotEqual(Predicate):
    """
    Inequality checking predicate

    Checks if a value extracted from context is not equal to the specified value.

    Args:
        expression: Path to value in context
        value: Value to compare against (should not match)

    Example:
        ```python
        # Exclude deleted items
        not_deleted = NotEqual("context.query.status", "deleted")

        # Require non-guest user
        not_guest = NotEqual("context.session.role", "guest")

        @app.action(predicates=[NotEqual("context.query.type", "admin")])
        async def non_admin_handler(context):
            pass
        ```
    """

    def __init__(self, expression: str, value: Any) -> None:
        """
        Initialize inequality predicate

        Args:
            expression: Path to value in context
            value: Value that should NOT match
        """
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if the expression evaluates to a different value

        Args:
            context: Current request context

        Returns:
            True if values are not equal, False if they are equal

        Raises:
            Does not raise exceptions; returns False on error
        """
        try:
            value = self._evaluate_expression(context)
            return self.__value != value
        except (KeyError, AttributeError, TypeError):
            return False
