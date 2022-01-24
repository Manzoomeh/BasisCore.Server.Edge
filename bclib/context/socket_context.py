from typing import TYPE_CHECKING
from bclib.utility import DictEx
from .context import Context

if TYPE_CHECKING:
    from .. import dispatcher
    from .. import listener


class SocketContext(Context):
    """Base class for dispatching web socket base request context"""

    def __init__(self, cms_object: dict,  dispatcher: 'dispatcher.IDispatcher', message_object: 'listener.Message', body: dict) -> None:
        super().__init__(dispatcher)
        self.cms = DictEx(cms_object) if cms_object else None
        self.url: str = self.cms.request.url if cms_object else None
        self.body = DictEx(body) if body else None
        self.message_object = message_object
        self.session_id = self.message_object.session_id
        self.message_type = self.message_object.type
        self.is_adhoc = False
