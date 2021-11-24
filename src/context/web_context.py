from typing import Any
from .request_context import RequestContext


class WebContext(RequestContext):
    def __init__(self, request, options: dict) -> None:
        super().__init__(request, options)
        self.process_async = True

    def generate_responce(self, result: Any) -> dict:
        ret_val = self.cms
        ret_val["cms"]["content"] = result
        ret_val["cms"]["webserver"] = {
            "index": "5",
            "headercode": "200 Ok",
            "mime": "text/html"
        }
        return ret_val
