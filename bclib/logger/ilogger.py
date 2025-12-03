"""Logger Interface

Generic logger interface for dependency injection.
Extends Python's logging.Logger for direct compatibility.
"""
import logging
from typing import Generic, TypeVar

T = TypeVar('T')


class ILogger(logging.Logger, Generic[T]):
    """
    Generic Logger Interface

    Interface for type-safe logger injection in constructors.
    The generic type parameter determines the logger name.
    Extends logging.Logger for direct compatibility with standard logging.

    Example:
        ```python
        class MyService:
            def __init__(self, logger: ILogger['MyService']):
                self.logger = logger

            def do_something(self):
                self.logger.info("Doing something")
                # Can use all standard logging.Logger methods
                self.logger.debug("Details here")
        ```
    """

    def __init__(self, name: str):
        """
        Initialize logger

        Args:
            name: Logger name
        """
        super().__init__(name)
