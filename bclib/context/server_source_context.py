from mailbox import Message
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher

from bclib.context.context import Context
from bclib.parser import HtmlParserEx


class ServerSourceContext(Context):
    """Base class for dispatching server base dbsource request context"""

    def __init__(self, cms_object: dict, dispatcher: 'IDispatcher', message_object: Message = None) -> None:
        super().__init__(dispatcher, True)
        parser = HtmlParserEx()
        self.raw_command = cms_object["command"]
        self.dmn_id = cms_object.get("dmnid")
        self.params = cms_object.get("params")
        parser.feed(self.raw_command)
        self.command = parser.get_dict()
        self.process_async = True

    def generate_response(self, result: Any) -> dict:
        return result
