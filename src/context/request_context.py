from abc import abstractmethod
from typing import Any, TYPE_CHECKING
from utility import DictEx
from .context import Context

if TYPE_CHECKING:
    import dispatcher


class RequestContext(Context):
    """Base class for dispatching http base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(dispatcher)
        self.__cms = DictEx(request)
        self.__url = self.__cms.request.url
        self.response: dict = None

    @property
    def url(self) -> str:
        return self.__url

    @property
    def cms(self) -> DictEx:
        return self.__cms

    @abstractmethod
    def generate_responce(self, result: Any) -> dict:
        return self.cms
