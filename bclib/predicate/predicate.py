"""
Predicate Module

This module provides the abstract base class for all predicates in the BasisCore framework.
Predicates are used to evaluate conditions against request contexts in a safe and efficient manner.

Features:
    - Abstract base class for all predicate implementations
    - Safe expression evaluation without using eval()
    - Efficient expression parsing with caching
    - Support for nested attribute and dictionary navigation

Example:
    ```python
    from bclib.predicate import Equal
    
    # Create a predicate to check if query parameter equals a value
    predicate = Equal("context.query.status", "active")
    
    # Check the predicate against a context
    is_match = await predicate.check_async(context)
    ```
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bclib.context import Context


class Predicate(ABC):
    """
    Base class for all predicates

    Predicates are used to evaluate conditions against request contexts.
    This abstract base class provides common functionality for expression evaluation
    and defines the interface that all predicates must implement.

    Attributes:
        expression: The expression string to evaluate (e.g., "context.query.user_id")

    Example:
        ```python
        class MyPredicate(Predicate):
            def __init__(self, expression: str, value: Any):
                super().__init__(expression)
                self.__value = value

            async def check_async(self, context: Context) -> bool:
                try:
                    actual = self._evaluate_expression(context)
                    return actual == self.__value
                except (KeyError, AttributeError):
                    return False
        ```
    """

    def __init__(self, expression: str) -> None:
        """
        Initialize the predicate with an expression

        Args:
            expression: Dot-notation path to evaluate (e.g., "context.query.status")
                       Can be None for predicates that don't evaluate expressions

        Note:
            Expression parsing is done once during initialization for performance.
            The parsed parts are cached in _parts and _start_idx.
        """
        super().__init__()
        self.expression = expression
        # Pre-parse expression for performance
        if expression:
            self._parts = expression.split('.')
            self._start_idx = 1 if self._parts[0] == 'context' else 0
        else:
            self._parts = []
            self._start_idx = 0

    def _evaluate_expression(self, context: 'Context') -> Any:
        """
        Safely evaluate expression without using eval()

        Navigates through context attributes/dictionaries using dot notation.
        Supports both attribute access (e.g., context.request) and dictionary access
        (e.g., context.query['user_id']).

        Args:
            context: Current request context

        Returns:
            The value at the expression path, or None if expression is empty

        Raises:
            KeyError: If a path component is not found
            AttributeError: If an attribute does not exist
            TypeError: If navigation through the path fails

        Example:
            ```python
            # Expression: "context.query.user_id"
            # Navigates: context -> query (dict) -> user_id (key)
            value = self._evaluate_expression(context)
            ```
        """
        if not self.expression:
            return None

        obj = context

        # Navigate through the path
        for part in self._parts[self._start_idx:]:
            # Handle dictionary access (like query, url_segments, form)
            if hasattr(obj, '__getitem__'):
                obj = obj[part]
            # Handle attribute access
            elif hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                raise KeyError(f"Path '{part}' not found")

        return obj

    @abstractmethod
    async def check_async(self, context: 'Context') -> bool:
        """
        Apply predicate checking logic

        This method must be implemented by all concrete predicate classes.

        Args:
            context: Current request context to evaluate

        Returns:
            True if the predicate condition is met, False otherwise

        Example:
            ```python
            async def check_async(self, context: Context) -> bool:
                try:
                    value = self._evaluate_expression(context)
                    return value == self.__expected_value
                except (KeyError, AttributeError):
                    return False
            ```
        """
