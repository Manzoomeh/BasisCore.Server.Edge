from bclib.utility import DictEx
from abc import ABC, abstractmethod
from typing import Callable

class BaseSignaler(ABC):
    def __init__(self, reset_cache_callback:"Callable", options:"DictEx"="None") -> None:
        super().__init__()
        self._callback = reset_cache_callback
        self._options = options
