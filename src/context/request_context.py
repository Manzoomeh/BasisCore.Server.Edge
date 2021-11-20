from typing import Any
from utility import DictEx
from .context import Context


class RequestContext(Context):
    """Base class for dispatching request base context"""

    def __init__(self, request: dict, options: dict) -> None:
        super().__init__(options)
        self.__request = DictEx(request)

    @property
    def request(self) -> DictEx:
        return self.__request

    def generate_responce(self, result: Any) -> dict:
        self.request["cms"]["http"] = {"Access-Control-Allow-Headers": " *"}
        return self.request
