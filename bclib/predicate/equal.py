"""
Equal Predicate Module

Provides equality checking predicate for comparing context values against expected values.
Uses safe expression evaluation without eval() for security.

Features:
    - Safe attribute and dictionary navigation
    - Support for nested paths (e.g., context.query.user_id)
    - Type-safe comparison
    - Graceful error handling

Example:
    ```python
    from bclib.predicate import Equal
    
    # Check if query parameter equals a value
    predicate = Equal("context.query.status", "active")
    is_match = await predicate.check_async(context)
    
    # Check if URL segment matches
    id_check = Equal("context.url_segments.id", "123")
    ```
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class Equal(Predicate):
    """
    Equality checking predicate

    Compares a value extracted from the context against an expected value.
    Safely evaluates nested attribute paths like 'context.query.user_id' or 
    'context.url_segments.id' without using eval().

    Attributes:
        expression: Dot-notation path to the value in context

    Args:
        expression: Path to evaluate (e.g., "context.query.status")
        value: Expected value to compare against

    Example:
        ```python
        # Check if query parameter 'status' equals 'active'
        predicate = Equal("context.query.status", "active")

        # Check if URL segment 'id' equals '123'
        id_predicate = Equal("context.url_segments.id", "123")

        # Use in decorator
        @app.action(predicates=[Equal("context.query.role", "admin")])
        async def admin_handler(context):
            pass
        ```
    """

    def __init__(self, expression: str, value: Any) -> None:
        """
        Initialize equality predicate

        Args:
            expression: Dot-notation path to value in context (e.g., "context.query.status")
            value: Expected value to compare against (can be any type)

        Note:
            Expression is parsed once during initialization for performance.
        """
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if the expression evaluates to the expected value

        Args:
            context: Current request context to evaluate

        Returns:
            True if the extracted value equals the expected value, False otherwise

        Raises:
            Does not raise exceptions; returns False on any error

        Example:
            ```python
            predicate = Equal("context.query.user_id", "123")
            result = await predicate.check_async(context)  # True if match
            ```
        """
        try:
            value = self._evaluate_expression(context)
            return self.__value == value
        except (KeyError, AttributeError, TypeError):
            return False
