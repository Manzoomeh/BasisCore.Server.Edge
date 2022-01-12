from typing import TYPE_CHECKING
from bclib.utility import HtmlParserEx, DictEx
from ..context.json_base_request_context import JsonBaseRequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class SourceContext(JsonBaseRequestContext):
    """Context for dbSource request"""

    def __init__(self, request: dict, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(request, dispatcher)
        parser = HtmlParserEx()
        html = self.cms.form.command
        parser.feed(html)
        self.__command = parser.get_dict_ex()
        self.process_async = True

    @ property
    def command(self) -> DictEx:
        return self.__command
