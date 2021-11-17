import json
from utility.DictEx import DictEx
from .request_context import RequestContext


class RESTfulContext(RequestContext):
    def __init__(self, request, options: dict) -> None:
        super().__init__(request, options)
        self.__body = DictEx(json.loads(self.request.request.body))
        self.process_async = True

    @property
    def body(self) -> DictEx:
        return self.__body
