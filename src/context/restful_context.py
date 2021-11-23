import json
from typing import Any
from utility.DictEx import DictEx
from .request_context import RequestContext


class RESTfulContext(RequestContext):
    def __init__(self, request, options: dict) -> None:
        super().__init__(request, options)
        self.__body = DictEx(json.loads(self.cms.request.body)
                             ) if self.cms.request.body else None
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
