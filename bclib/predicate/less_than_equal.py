"""
LessThanEqual Predicate Module

Provides comparison predicate for checking if a value is less than or equal to a threshold.

Features:
    - Numeric comparison (value <= threshold)
    - Safe type handling
    - Graceful error handling

Example:
    ```python
    from bclib.predicate import LessThanEqual
    
    # Check if age is 65 or younger
    predicate = LessThanEqual("context.query.age", 65)
    ```
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class LessThanEqual(Predicate):
    """
    Less than or equal comparison predicate

    Checks if a numeric value from context is less than or equal to the threshold.

    Args:
        expression: Path to numeric value in context
        value: Threshold value for comparison

    Example:
        ```python
        # Check maximum age limit
        max_age = LessThanEqual("context.query.age", 65)

        # Check if quantity is within limit
        max_qty = LessThanEqual("context.form.quantity", 100)
        ```
    """

    def __init__(self, expression: str, value: int) -> None:
        """
        Initialize less than or equal predicate

        Args:
            expression: Path to numeric value in context
            value: Maximum threshold (inclusive)
        """
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if value is less than or equal to threshold

        Args:
            context: Current request context

        Returns:
            True if extracted_value <= threshold, False otherwise

        Raises:
            Does not raise exceptions; returns False on error
        """
        try:
            value = self._evaluate_expression(context)
            return self.__value >= value
        except (KeyError, AttributeError, TypeError, ValueError):
            return False
