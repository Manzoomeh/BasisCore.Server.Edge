from typing import Any, TYPE_CHECKING

from bclib.utility import HttpMimeTypes
from ..context.request_context import RequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class WebContext(RequestContext):
    def __init__(self, cms_object: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(cms_object, dispatcher)
        self.process_async = True
        self.mime = HttpMimeTypes.HTML
