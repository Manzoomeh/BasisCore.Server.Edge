from abc import abstractmethod
from typing import Any, TYPE_CHECKING
from utility import DictEx
from .context import Context

if TYPE_CHECKING:
    import dispatcher
    import listener


class RequestContext(Context):
    """Base class for dispatching request base context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher', message: 'listener.Message') -> None:
        super().__init__(dispatcher)
        self.__cms = DictEx(request)
        self.__message = message
        self.response: dict = None

    @property
    def message(self) -> 'listener.Message':
        return self.__message

    @property
    def url(self) -> str:
        return self.cms.request.url

    @property
    def cms(self) -> DictEx:
        return self.__cms

    @abstractmethod
    def generate_responce(self, result: Any) -> dict:
        return self.cms
