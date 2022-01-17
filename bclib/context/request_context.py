from abc import abstractmethod
from typing import Any, TYPE_CHECKING
from bclib.listener.http_listener import HttpBaseDataName, HttpBaseDataType
from bclib.utility import DictEx, HttpStatusCodes, HttpMimeTypes, ResponseType
from ..context.context import Context

if TYPE_CHECKING:
    from .. import dispatcher


class RequestContext(Context):
    """Base class for dispatching http base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(dispatcher)
        self.cms = DictEx(request)
        self.url: str = self.cms.request.url
        self.query: DictEx = self.cms.query
        self.form: DictEx = self.cms.form
        self.__headers: dict = None
        self.responce_type: ResponseType = ResponseType.RENDERED
        self.status_code: HttpStatusCodes = HttpStatusCodes.OK
        self.mime = HttpMimeTypes.HTML

    def add_header(self, key: str, value: str) -> None:
        """Adding item to response header"""

        if self.__headers is None:
            self.__headers = dict()
        if key not in self.__headers:
            self.__headers[key] = [value]
        else:
            self.__headers[key].append(value)

    @abstractmethod
    def generate_responce(self, result: Any) -> dict:
        ret_val = self.cms
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER] = {
            "index": self.responce_type.value,
            "headercode": self.status_code.value,
            "mime": self.mime
        }
        if self.__headers is not None:
            RequestContext.__add_user_defined_headers(ret_val, self.__headers)
        return ret_val

    @staticmethod
    def __add_user_defined_headers(response: dict, headers: dict) -> None:
        """Adding user defined header to response"""

        if HttpBaseDataType.CMS not in response:
            response[HttpBaseDataType.CMS] = {}
        if HttpBaseDataName.HTTP not in response[HttpBaseDataType.CMS]:
            response[HttpBaseDataType.CMS][HttpBaseDataName.HTTP] = {}
        http = response[HttpBaseDataType.CMS][HttpBaseDataName.HTTP]
        for key, value in headers.items():
            if key in http:
                current_value = http[key] if isinstance(
                    http[key], list) else [http[key]]
                new_value = current_value + value
            else:
                new_value = value

            http[key] = ",".join(new_value)
