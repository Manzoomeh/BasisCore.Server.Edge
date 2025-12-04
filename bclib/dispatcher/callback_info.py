"""CallbackInfo - Encapsulates handler callback with predicates and routing logic"""
import re
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from bclib.exception import ShortCircuitErr

if TYPE_CHECKING:
    from bclib.context.context import Context

from bclib.predicate.predicate import Predicate


class CallbackInfo:
    """
    Encapsulates a handler callback with its predicates and provides routing utilities

    This class manages the association between a handler function and its routing predicates,
    providing methods for execution, URL pattern extraction, and handler matching.

    Attributes:
        __async_callback: The async handler function to execute
        __predicates: List of predicates that must pass for handler execution
    """

    def __init__(self, predicates: list[Predicate], async_callback: Callable[['Context'], Awaitable[dict]]) -> None:
        """
        Initialize CallbackInfo with predicates and handler

        Args:
            predicates: List of predicates for routing conditions
            async_callback: Async handler function to execute when predicates pass
        """
        self.__async_callback = async_callback
        self.__predicates = predicates

    async def try_execute_async(self, context: 'Context') -> dict:
        """
        Try to execute the handler if all predicates pass

        Args:
            context: The request context to validate and pass to handler

        Returns:
            Result from handler execution, or error response if predicates fail
        """
        result: dict = None
        for predicate in self.__predicates:
            try:
                if not await predicate.check_async(context):
                    break
            except ShortCircuitErr as ex:
                result = context.generate_error_response(ex)
                break
        else:
            result = await self.__async_callback(context)
        return result

    def get_url_patterns(self) -> list[str]:
        """
        Extract URL patterns from predicates and convert to regex patterns

        Converts URL predicates with parameter placeholders (e.g., '/api/users/:id')
        into regex patterns (e.g., '/api/users/(?P<id>[^/]+)') for routing.

        Returns:
            List of regex patterns for URL matching
        """
        from bclib.predicate.url import Url

        patterns = []
        for predicate in self.__predicates:
            if isinstance(predicate, Url):
                pattern = predicate.expression
                # Convert :param to (?P<param>[^/]+) for named regex groups
                regex_pattern = re.sub(r':(\w+)', r'(?P<\1>[^/]+)', pattern)
                patterns.append(regex_pattern)
        return patterns

    def matches_handler(self, handler: Callable) -> bool:
        """
        Check if this callback info wraps the given handler

        Used for handler unregistration to find the callback info that wraps
        a specific handler function.

        Args:
            handler: The original handler function to match

        Returns:
            True if this callback's async_callback wraps the given handler
        """
        return (hasattr(self.__async_callback, '__wrapped__') and
                self.__async_callback.__wrapped__ is handler)
