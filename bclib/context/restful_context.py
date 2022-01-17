import json
from typing import TYPE_CHECKING
from bclib.utility import DictEx
from ..context.json_base_request_context import JsonBaseRequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class RESTfulContext(JsonBaseRequestContext):
    def __init__(self, request: dict, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(request, dispatcher)
        self.body = DictEx(self.cms.form) if self.cms.form else DictEx(
            json.loads(self.cms.request.body)) if self.cms.request.body else None
