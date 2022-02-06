from abc import ABC, abstractmethod
from bclib.context import Context


class Predicate(ABC):
    """Base class for predicate"""

    def __init__(self, expression: str) -> None:
        super().__init__()
        self.exprossion = expression

    @abstractmethod
    async def check_async(self, context: Context) -> bool:
        """Applay cheking for predicate"""
