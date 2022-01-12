from abc import abstractmethod
from typing import Any, TYPE_CHECKING
from bclib.listener.http_listener import HttpBaseDataName, HttpBaseDataType

from bclib.utility import DictEx
from ..context.context import Context

if TYPE_CHECKING:
    from .. import dispatcher


class RequestContext(Context):
    """Base class for dispatching http base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(dispatcher)
        self.__cms = DictEx(request)
        self.__url = self.__cms.request.url
        self.headers: dict = None
        self.index = "5"
        self.status_code = "200 OK"
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

        if self.headers is None:
            self.headers = dict()
        if key not in self.headers:
            self.headers[key] = [value]
        else:
            self.headers[key].append(value)

    @abstractmethod
    def generate_responce(self, result: Any) -> dict:
        ret_val = self.cms
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER] = {
            "index": self.index,
            "headercode": self.status_code,
            "mime": self.mime
        }
        return ret_val
