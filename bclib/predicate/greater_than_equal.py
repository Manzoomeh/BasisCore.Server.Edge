"""
GreaterThanEqual Predicate Module

Provides comparison predicate for checking if a value is greater than or equal to a threshold.

Features:
    - Numeric comparison (value >= threshold)
    - Safe type handling
    - Graceful error handling

Example:
    ```python
    from bclib.predicate import GreaterThanEqual
    
    # Check if age is 18 or older
    predicate = GreaterThanEqual("context.query.age", 18)
    ```
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class GreaterThanEqual(Predicate):
    """
    Greater than or equal comparison predicate

    Checks if a numeric value from context is greater than or equal to the threshold.

    Args:
        expression: Path to numeric value in context
        value: Threshold value for comparison

    Example:
        ```python
        # Check minimum age requirement
        min_age = GreaterThanEqual("context.query.age", 18)

        # Check if quantity meets minimum
        min_qty = GreaterThanEqual("context.form.quantity", 1)
        ```
    """

    def __init__(self, expression: str, value: int) -> None:
        """
        Initialize greater than or equal predicate

        Args:
            expression: Path to numeric value in context
            value: Minimum threshold (inclusive)
        """
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if value is greater than or equal to threshold

        Args:
            context: Current request context

        Returns:
            True if extracted_value >= threshold, False otherwise

        Raises:
            Does not raise exceptions; returns False on error
        """
        try:
            value = self._evaluate_expression(context)
            return self.__value <= value
        except (KeyError, AttributeError, TypeError, ValueError):
            return False
