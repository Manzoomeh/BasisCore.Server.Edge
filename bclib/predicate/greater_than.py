"""
GreaterThan Predicate Module

Provides comparison predicate for checking if a value is greater than a threshold.

Features:
    - Numeric comparison (value > threshold)
    - Safe type handling
    - Graceful error handling

Example:
    ```python
    from bclib.predicate import GreaterThan
    
    # Check if age is greater than 18
    predicate = GreaterThan("context.query.age", 18)
    ```
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class GreaterThan(Predicate):
    """
    Greater than comparison predicate

    Checks if a numeric value from context is greater than the specified threshold.

    Args:
        expression: Path to numeric value in context
        value: Threshold value for comparison

    Example:
        ```python
        # Check if user age is greater than 18
        age_check = GreaterThan("context.query.age", 18)

        # Check if price exceeds limit
        price_check = GreaterThan("context.form.price", 1000)

        @app.handler(predicates=[GreaterThan("context.query.score", 80)])
        async def high_score_handler(context):
            pass
        ```
    """

    def __init__(self, expression: str, value: int) -> None:
        """
        Initialize greater than predicate

        Args:
            expression: Path to numeric value in context
            value: Threshold for comparison
        """
        super().__init__(expression)
        self.__value = value

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if extracted value is greater than threshold

        Args:
            context: Current request context

        Returns:
            True if extracted_value > threshold, False otherwise

        Raises:
            Does not raise exceptions; returns False on error
        """
        try:
            value = self._evaluate_expression(context)
            return self.__value < value
        except (KeyError, AttributeError, TypeError, ValueError):
            return False
