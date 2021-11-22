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

    def generate_responce(self, result: Any) -> dict:
        self.cms["cms"]["http"] = {"Access-Control-Allow-Headers": " *"}
        return self.cms
