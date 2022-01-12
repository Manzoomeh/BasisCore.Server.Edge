from typing import Any, TYPE_CHECKING

from bclib.listener.http_listener import HttpBaseDataName, HttpBaseDataType
from ..context.request_context import RequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class WebContext(RequestContext):
    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(request, dispatcher)
        self.process_async = True
        self.mime = "text/html"

    def generate_responce(self, result: Any) -> dict:
        ret_val = super().generate_responce(result)
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT] = result
        return ret_val
