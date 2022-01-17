from typing import TYPE_CHECKING
from bclib.utility import DictEx
from ..context.context import Context

if TYPE_CHECKING:
    from .. import dispatcher
    from .. import listener


class SocketContext(Context):
    """Base class for dispatching web socket base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher', message: 'listener.Message') -> None:
        super().__init__(dispatcher)
        self.cms = DictEx(request) if request else None
        self.url: str = self.cms.request.url if request else None
        self.message = message
        self.session_id = self.message.session_id
        self.message_type = self.message.type
