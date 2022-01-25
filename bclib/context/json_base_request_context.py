import json
from typing import Any, TYPE_CHECKING
from struct import error

from bclib.utility import HttpMimeTypes, HttpStatusCodes
from bclib.listener.http_listener import HttpBaseDataName, HttpBaseDataType
from ..context.request_context import RequestContext
from bclib.exception import ShortCircuitErr

if TYPE_CHECKING:
    from .. import dispatcher


class JsonBaseRequestContext(RequestContext):
    """Base class for dispatching http json base request context"""

    def __init__(self, cms_object: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(cms_object, dispatcher)
        self.mime = HttpMimeTypes.JSON

    def generate_error_responce(self, error: error) -> dict:
        """Generate error responce from process result"""
        error_code = -1
        if isinstance(error, ShortCircuitErr):
            self.status_code = error.status_code
            error_code = error.error_code
        else:
            self.status_code = HttpStatusCodes.INTERNAL_SERVER_ERROR

        content = {"error_code": error_code, "error_message": str(error)}
        return self.generate_responce(content)

    def generate_responce(self, result: dict) -> dict:
        """Generate responce from process result"""

        ret_val = super().generate_responce(result)
        ret_val[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT] = json.dumps(
            result)
        return ret_val
