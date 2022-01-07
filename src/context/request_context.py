from abc import abstractmethod
from typing import Any, TYPE_CHECKING

from listener import HttpBaseDataType, HttpBaseDataName
from qam_test import HttpBaseDataType
from utility import DictEx
from .context import Context

if TYPE_CHECKING:
    import dispatcher


class RequestContext(Context):
    """Base class for dispatching http base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(dispatcher)
        self.__cms = DictEx(request)
        self.__url = self.__cms.request.url
        self.response: dict = None
        self.index = "5"
        self.headercode = "200 OK"
        self.mime = "text/html"

    @property
    def query(self) -> DictEx:
        return self.__cms.query

    @property
    def form(self) -> DictEx:
        return self.__cms.form

    @property
    def url(self) -> str:
        return self.__url

    @property
    def cms(self) -> DictEx:
        return self.__cms

    def add_header(self, key: str, value: str) -> None:
        """Adding item to response header"""

        if self.response is None:
            self.response = {"cms": {}}
        if HttpBaseDataType.Cms not in self.response["cms"]:
            self.response["cms"][HttpBaseDataType.Cms] = dict()
        if HttpBaseDataName.HTTP not in self.response["cms"][HttpBaseDataType.Cms]:
            self.response["cms"][HttpBaseDataType.Cms][HttpBaseDataName.HTTP] = dict()

        http = self.response["cms"][HttpBaseDataType.Cms][HttpBaseDataName.HTTP]
        if key not in http:
            http[key] = value
        else:
            old_value = http[key]
            if isinstance(old_value, list):
                old_value.append(value)
            else:
                http[key] = [old_value, value]

    @abstractmethod
    def generate_responce(self, result: Any) -> dict:
        ret_val = self.cms
        ret_val["cms"]["webserver"] = {
            "index": self.index,
            "headercode": self.headercode,
            "mime": self.mime
        }
        return ret_val
