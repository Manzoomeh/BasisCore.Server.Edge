import json
from typing import Any, TYPE_CHECKING
from utility import BasisCoreHtmlParser, DictEx
from .request_context import RequestContext

if TYPE_CHECKING:
    import dispatcher


class SourceContext(RequestContext):
    """Context for dbSource request"""

    def __init__(self, request: dict, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(request, dispatcher)
        parser = BasisCoreHtmlParser()
        html = self.cms.form.command
        parser.feed(html)
        self.__command = parser.get_dict_ex()
        self.process_async = True

    @property
    def command(self) -> DictEx:
        return self.__command

    def generate_responce(self, result: Any) -> dict:
        ret_val = self.cms
        ret_val["cms"]["content"] = json.dumps(result)
        ret_val["cms"]["webserver"] = {
            "index": "5",
            "headercode": "200 Ok",
            "mime": "application/json"
        }
        return ret_val
