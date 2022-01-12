from abc import ABC, abstractmethod
from ..context import Context


class Predicate(ABC):
    """Base class for predicate"""

    def __init__(self, expression: str) -> None:
        super().__init__()
        self.exprossion = expression

    @abstractmethod
    def check(self, context: Context) -> bool:
        """Applay cheking for predicate"""
