from abc import abstractmethod
from typing import Any
from utility import DictEx
from .context import Context


class RequestContext(Context):
    """Base class for dispatching request base context"""

    def __init__(self, request: dict, options: dict) -> None:
        super().__init__(options)
        self.__cms = DictEx(request)

    @property
    def cms(self) -> DictEx:
        return self.__cms

    @abstractmethod
    def generate_responce(self, result: Any, settings: Any) -> dict:
        return self.cms

    @staticmethod
    def update_setting(response: dict, setting: dict):
        for key, value in setting["cms"].items():
            response[key].update(value)
