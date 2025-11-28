"""
Callback Predicate Module

Provides custom callback-based predicate for complex validation logic.

Features:
    - Execute custom async functions as predicates
    - Full access to context for complex logic
    - Preserves ShortCircuitErr for control flow

Example:
    ```python
    from bclib.predicate import Callback
    
    async def custom_check(context):
        # Complex validation logic
        return context.user.is_active and context.user.has_permission('edit')
    
    predicate = Callback(custom_check)
    ```
"""

from typing import TYPE_CHECKING, Callable, Coroutine

if TYPE_CHECKING:
    from bclib.context import Context

from bclib.exception import ShortCircuitErr
from bclib.predicate.predicate import Predicate


class Callback(Predicate):
    """
    Custom callback-based predicate

    Allows executing custom async functions as predicates for complex validation
    logic that cannot be expressed with standard predicates.

    Args:
        callback: Async function that takes Context and returns bool

    Example:
        ```python
        async def is_premium_user(context):
            user_id = context.query.get('user_id')
            user = await get_user(user_id)
            return user.subscription == 'premium'

        predicate = Callback(is_premium_user)

        @app.action(predicates=[predicate])
        async def premium_feature(context):
            pass
        ```
    """

    def __init__(self, callback: 'Callable[[Context],Coroutine[bool]]') -> None:
        """
        Initialize callback predicate

        Args:
            callback: Async function taking Context and returning bool

        Note:
            Callback should be an async function for proper execution.
        """
        super().__init__(None)
        self.__callback = callback

    async def check_async(self, context: 'Context') -> bool:
        """
        Execute the callback function

        Args:
            context: Current request context passed to callback

        Returns:
            Result of callback execution

        Raises:
            ShortCircuitErr: Re-raised to preserve control flow

        Note:
            All other exceptions are caught and return False.
        """
        try:
            return await self.__callback(context)
        except ShortCircuitErr:
            raise
        except Exception:
            return False
