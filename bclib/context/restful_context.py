import json
from typing import TYPE_CHECKING
from bclib.utility import DictEx
from ..context.json_base_request_context import JsonBaseRequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class RESTfulContext(JsonBaseRequestContext):
    def __init__(self, request: dict, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(request, dispatcher)
        if self.cms.form:
            self.__body = DictEx(self.cms.form)
        elif self.cms.request.body:
            self.__body = DictEx(json.loads(self.cms.request.body))
        else:
            self.__body = None

    @property
    def body(self) -> DictEx:
        return self.__body
