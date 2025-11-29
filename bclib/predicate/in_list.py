"""
InList Predicate Module

Provides predicate for checking if a value is in a list of allowed values.

Features:
    - Membership testing (value in allowed_list)
    - Support for any comparable types
    - Efficient lookup

Example:
    ```python
    from bclib.predicate import InList
    
    # Check if status is one of allowed values
    predicate = InList("context.query.status", "active", "pending", "approved")
    ```
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class InList(Predicate):
    """
    List membership checking predicate

    Checks if a value from context is in a list of allowed values.

    Args:
        expression: Path to value in context
        *items: Variable number of allowed values

    Example:
        ```python
        # Check if role is admin or moderator
        role_check = InList("context.query.role", "admin", "moderator")

        # Check if status is valid
        status_check = InList(
            "context.query.status",
            "active", "pending", "approved", "rejected"
        )

        @app.handler(predicates=[InList("context.query.type", "A", "B", "C")])
        async def type_handler(context):
            pass
        ```
    """

    def __init__(self, expression: str, *items: Any) -> None:
        """
        Initialize list membership predicate

        Args:
            expression: Path to value in context
            *items: Allowed values (variable arguments)
        """
        super().__init__(expression)
        self.__items = items

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if value is in allowed list

        Args:
            context: Current request context

        Returns:
            True if extracted value is in allowed items, False otherwise

        Raises:
            Does not raise exceptions; returns False on error
        """
        try:
            value = self._evaluate_expression(context)
            return value in self.__items
        except (KeyError, AttributeError, TypeError):
            return False
