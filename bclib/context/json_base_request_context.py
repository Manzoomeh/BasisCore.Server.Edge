import json
from typing import TYPE_CHECKING

from bclib.utility import HttpMimeTypes
from bclib.context.request_context import RequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class JsonBaseRequestContext(RequestContext):
    """Base class for dispatching http json base request context"""

    def __init__(self, cms_object: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(cms_object, dispatcher)
        self.mime = HttpMimeTypes.JSON

    def generate_error_response(self,  exception: Exception) -> dict:
        """Generate error response from process result"""
        error_object, self.status_code = self._generate_error_object(exception)
        self.mime = HttpMimeTypes.JSON
        return self.generate_response(error_object)

    def generate_response(self, content: dict) -> dict:
        """Generate response from process content"""

        return super().generate_response(json.dumps(content))
