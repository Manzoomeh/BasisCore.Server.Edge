import json
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    import dispatcher
    import listener
from utility import DictEx
from .request_context import RequestContext


class RESTfulContext(RequestContext):
    def __init__(self, request: dict, dispatcher: 'dispatcher.IDispatcher',  message: 'listener.Message') -> None:
        super().__init__(request, dispatcher, message)
        if self.cms.form:
            self.__body = DictEx(self.cms.form)
        elif self.cms.request.body:
            self.__body = DictEx(json.loads(self.cms.request.body))
        else:
            self.__body = None
        self.process_async = True

    @property
    def body(self) -> DictEx:
        return self.__body

    def generate_responce(self, result: Any) -> dict:
        ret_val = self.cms
        ret_val["cms"]["content"] = json.dumps(result)
        ret_val["cms"]["webserver"] = {
            "index": "5",
            "headercode": "200 Ok",
            "mime": "application/json"
        }
        return ret_val
