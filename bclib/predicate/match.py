"""
Match Predicate Module

Provides regex pattern matching predicate for string validation.

Features:
    - Regular expression matching
    - Pre-compiled patterns for performance
    - Safe string conversion

Example:
    ```python
    from bclib.predicate import Match
    
    # Check if email matches pattern
    email_pattern = Match("context.query.email", r"^[\w.-]+@[\w.-]+\.\w+$")
    ```
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.predicate.predicate import Predicate


class Match(Predicate):
    """
    Regular expression matching predicate

    Checks if a string value from context matches a regular expression pattern.
    Pattern is compiled once during initialization for performance.

    Args:
        expression: Path to string value in context
        value: Regular expression pattern string

    Example:
        ```python
        # Validate email format
        email = Match("context.query.email", r"^[\w.-]+@[\w.-]+\.\w+$")

        # Validate phone number
        phone = Match("context.form.phone", r"^\d{3}-\d{3}-\d{4}$")

        # Check if username is alphanumeric
        username = Match("context.query.user", r"^[a-zA-Z0-9_]+$")

        @app.action(predicates=[Match("context.query.code", r"^[A-Z]{3}\d{3}$")])
        async def code_handler(context):
            pass
        ```
    """

    def __init__(self, expression: str, value: str) -> None:
        """
        Initialize regex matching predicate

        Args:
            expression: Path to string value in context
            value: Regular expression pattern

        Note:
            Pattern is compiled once during initialization for performance.
        """
        super().__init__(expression)
        self.__compiled_regex = re.compile(value)

    async def check_async(self, context: 'Context') -> bool:
        """
        Check if value matches the regex pattern

        Args:
            context: Current request context

        Returns:
            True if value matches pattern, False otherwise

        Raises:
            Does not raise exceptions; returns False on error

        Note:
            Value is converted to string before matching.
        """
        try:
            value = self._evaluate_expression(context)
            return self.__compiled_regex.match(str(value)) is not None
        except (KeyError, AttributeError, TypeError):
            return False
