from abc import abstractmethod
from typing import Any, TYPE_CHECKING
from listener.message_type import MessageType
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
        self.__url = self.__cms if request else None
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


class RequestContext(Context):
    """Base class for dispatching http base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher', message: 'listener.Message') -> None:
        super().__init__(dispatcher)
        self.__cms = DictEx(request)
        self.response: dict = None

    @property
    def url(self) -> str:
        return self.cms.request.url

    @property
    def cms(self) -> DictEx:
        return self.__cms

    @abstractmethod
    def generate_responce(self, result: Any) -> dict:
        return self.cms
