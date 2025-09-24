from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bclib.context.context import Context


class Predicate(ABC):
    """Base class for predicate"""

    def __init__(self, expression: 'str') -> 'None':
        super().__init__()
        self.expression = expression

    @abstractmethod
    async def check_async(self, context: 'Context') -> 'bool':
        """Apply checking for predicate"""
