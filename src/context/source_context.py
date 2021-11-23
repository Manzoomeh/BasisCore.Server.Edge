import json
from typing import Any
from utility import BasisCoreHtmlParser
from utility.DictEx import DictEx
from .request_context import RequestContext


class SourceContext(RequestContext):
    """Context for dbSource request"""

    def __init__(self, request, options: dict) -> None:
        super().__init__(request, options)
        parser = BasisCoreHtmlParser()
        html = self.cms.form.command
        parser.feed(html)
        self.__command = parser.get_dict_ex()
        self.process_async = True

    @property
    def command(self) -> DictEx:
        return self.__command

    def generate_responce(self, result: Any, settings: Any) -> dict:
        ret_val = self.cms
        ret_val["cms"]["content"] = json.dumps(result)
        ret_val["cms"]["webserver"] = {
            "index": "5",
            "headercode": "200 Ok",
            "mime": "application/json"
        }
        if settings is not None:
            RequestContext.update_setting(ret_val, settings)
        return ret_val
