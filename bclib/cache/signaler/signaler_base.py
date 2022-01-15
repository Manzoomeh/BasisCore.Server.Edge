"""base class for signaller"""
from abc import ABC
from typing import Callable


class SignalerBase(ABC):
    """base class for signaller"""

    def __init__(self, options: dict, callback: 'Callable[[list[str]], None]') -> None:
        super().__init__()
        self._options = options
        self._callback = callback
