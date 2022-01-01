from abc import abstractmethod
import json
from typing import Any, TYPE_CHECKING
from .request_context import RequestContext

if TYPE_CHECKING:
    import dispatcher


class JsonBaseRequestContext(RequestContext):
    """Base class for dispatching http json base request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(request, dispatcher)
        self.mime = "application/json"

    @abstractmethod
    def generate_responce(self, result: Any) -> dict:
        ret_val = super().generate_responce(result)
        ret_val["cms"]["content"] = json.dumps(result)
        return ret_val
