from typing import TYPE_CHECKING
from utility import DictEx
from .context import Context

if TYPE_CHECKING:
    import dispatcher
    import listener


class SocketContext(Context):
    """Base class for dispatching web socket base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher', message: 'listener.Message') -> None:
        super().__init__(dispatcher)
        self.__cms = DictEx(request) if request else None
        self.__url = self.__cms.request.url if request else None
        self.__message = message

    @property
    def message(self) -> 'listener.Message':
        return self.__message

    @property
    def session_id(self) -> str:
        return self.__message.session_id

    @property
    def message_type(self) -> 'listener.MessageType':
        return self.__message.type

    @property
    def url(self) -> str:
        return self.__url

    @property
    def cms(self) -> DictEx:
        return self.__cms
