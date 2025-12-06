"""
Between Predicate Module

Provides range checking predicate for numeric values (exclusive bounds).

Features:
    - Checks if value is within range (min < value < max)
    - Automatic type conversion to int
    - Safe expression evaluation

Example:
    ```python
    from bclib.predicate import Between
    
    # Check if age is between 18 and 65 (exclusive)
    predicate = Between("context.query.age", 18, 65)
    ```
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class Between(Predicate):
    """
    Range checking predicate (exclusive bounds)

    Checks if a numeric value from context is within the specified range.
    Uses exclusive comparison (min < value < max).

    Args:
        expression: Path to numeric value in context
        min_value: Minimum value (exclusive)
        max_value: Maximum value (exclusive)

    Example:
        ```python
        # Check if age is between 18 and 65
        age_check = Between("context.query.age", 18, 65)

        # Check if score is in valid range
        score_check = Between("context.form.score", 0, 100)
        ```
    """

    def __init__(self, expression: str, min_value: int, max_value: int) -> None:
        """
        Initialize range checking predicate

        Args:
            expression: Path to numeric value in context
            min_value: Minimum bound (exclusive)
            max_value: Maximum bound (exclusive)
        """
        super().__init__(expression)
        self.__min_value = min_value
        self.__max_value = max_value

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if value is within range

        Args:
            context: Current request context

        Returns:
            True if min_value < value < max_value, False otherwise

        Raises:
            Does not raise exceptions; returns False on error or invalid type

        Note:
            Value is converted to int; conversion errors return False.
        """
        try:
            value = self._evaluate_expression(context)
            return self.__min_value < int(value) < self.__max_value
        except (KeyError, AttributeError, TypeError, ValueError):
            return False
