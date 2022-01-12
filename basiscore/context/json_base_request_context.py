import json
from typing import Any, TYPE_CHECKING
from basiscore.listener.http_listener import HttpBaseDataName, HttpBaseDataType
from ..context.request_context import RequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class JsonBaseRequestContext(RequestContext):
    """Base class for dispatching http json base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(request, dispatcher)
        self.mime = "application/json"

    def generate_responce(self, result: Any) -> dict:
        ret_val = super().generate_responce(result)
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT] = json.dumps(
            result)
        return ret_val
