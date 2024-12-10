from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher

from bclib.parser.html.html_parser_ex import HtmlParserEx
from bclib.utility.dict_ex import DictEx
from bclib.context.context import Context


class ServerSourceContext(Context):
    """Base class for dispatching server base dbsource request context"""

    def __init__(self, cms_object: dict,  dispatcher: 'IDispatcher') -> None:
        super().__init__(dispatcher)
        parser = HtmlParserEx()
        self.raw_command = cms_object["command"]
        self.dmn_id = cms_object["dmnid"] if "dmnid" in cms_object else None
        self.params = DictEx(
            cms_object["params"]) if "params" in cms_object else None
        parser.feed(self.raw_command)
        self.command = parser.get_dict_ex()
        self.process_async = True

    def generate_response(self, result: Any) -> dict:
        return result
