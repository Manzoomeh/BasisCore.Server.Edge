"""
HasValue Predicate Module

Provides predicate for checking if a value exists and is not empty.

Features:
    - Checks for None, empty strings, and falsy values
    - Handles whitespace-only strings
    - Safe evaluation

Example:
    ```python
    from bclib.predicate import HasValue
    
    # Check if user_id parameter exists and has a value
    predicate = HasValue("context.query.user_id")
    ```
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class HasValue(Predicate):
    """
    Value existence checking predicate

    Checks if a value from context exists and is not empty. Handles special cases
    like None, empty strings, and whitespace-only strings.

    Args:
        expression: Path to value in context to check

    Example:
        ```python
        # Require user_id parameter
        has_user = HasValue("context.query.user_id")

        # Require session token
        has_token = HasValue("context.session.token")

        @app.handler(predicates=[HasValue("context.query.api_key")])
        async def protected_handler(context):
            pass
        ```
    """

    def __init__(self, expression: str) -> None:
        """
        Initialize value existence predicate

        Args:
            expression: Path to value in context to check for existence
        """
        super().__init__(expression)

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if value exists and is not empty

        Args:
            context: Current request context

        Returns:
            True if value exists and is not None/empty/whitespace, False otherwise

        Raises:
            Does not raise exceptions; returns False on error

        Note:
            For strings, checks that value is not empty and not just whitespace.
            For other types, checks boolean truthiness.
        """
        try:
            value = self._evaluate_expression(context)
            if value is None:
                return False
            if isinstance(value, str):
                return bool(value and not value.isspace())
            return bool(value)
        except (KeyError, AttributeError, TypeError):
            return False
