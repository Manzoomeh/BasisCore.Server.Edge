"""
LessThan Predicate Module

Provides comparison predicate for checking if a value is less than a threshold.

Features:
    - Numeric comparison (value < threshold)
    - Safe type handling
    - Graceful error handling

Example:
    ```python
    from bclib.predicate import LessThan
    
    # Check if age is less than 65
    predicate = LessThan("context.query.age", 65)
    ```
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class LessThan(Predicate):
    """
    Less than comparison predicate

    Checks if a numeric value from context is less than the specified threshold.

    Args:
        expression: Path to numeric value in context
        value: Threshold value for comparison

    Example:
        ```python
        # Check if age is under 65
        age_check = LessThan("context.query.age", 65)

        # Check if price is below limit
        price_check = LessThan("context.form.price", 10000)

        @app.handler(predicates=[LessThan("context.query.count", 100)])
        async def limited_handler(context):
            pass
        ```
    """

    def __init__(self, expression: str, value: int) -> None:
        """
        Initialize less than predicate

        Args:
            expression: Path to numeric value in context
            value: Threshold for comparison
        """
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if extracted value is less than threshold

        Args:
            context: Current request context

        Returns:
            True if extracted_value < threshold, False otherwise

        Raises:
            Does not raise exceptions; returns False on error
        """
        try:
            value = self._evaluate_expression(context)
            return self.__value > value
        except (KeyError, AttributeError, TypeError, ValueError):
            return False
