from abc import abstractmethod
from typing import Any
from utility import DictEx
from .context import Context


class RequestContext(Context):
    """Base class for dispatching request base context"""

    def __init__(self, request: dict, options: dict) -> None:
        super().__init__(options)
        self.__cms = DictEx(request)
        self.response = None

    @property
    def cms(self) -> DictEx:
        return self.__cms

    @abstractmethod
    def generate_responce(self, result: Any) -> dict:
        return self.cms
