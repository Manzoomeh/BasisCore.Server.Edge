from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .. import dispatcher

from bclib.utility import HtmlParserEx, DictEx
from ..context.context import Context


class ServerSourceContext(Context):
    """Base class for dispatching server base dbsource request context"""

    def __init__(self, request: dict,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(dispatcher)
        parser = HtmlParserEx()
        self.raw_command = request["command"]
        self.dmn_id = request["dmnid"] if "dmnid" in request else None
        self.params = DictEx(
            request["params"]) if "params" in request else None
        html = self.raw_command
        parser.feed(html)
        self.command = parser.get_dict_ex()
        self.process_async = True

    def generate_responce(self, result: Any) -> dict:
        return result
