from typing import TYPE_CHECKING

from bclib.utility import HtmlParserEx, DictEx
from ..context.json_base_request_context import JsonBaseRequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class SourceContext(JsonBaseRequestContext):
    """Context for dbSource request"""

    def __init__(self, cms_object: dict, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(cms_object, dispatcher)
        parser = HtmlParserEx()
        html = self.cms.form.command
        parser.feed(html)
        self.command = parser.get_dict_ex()
        self.params: DictEx = None
        if "params" in self.command:
            if len(self.command.params) > 0 and "add" in self.command.params[0]:
                tmp_dic = dict()
                for item in self.command.params[0].add:
                    tmp_dic[item.name] = item.value
                self.params = DictEx(tmp_dic)
        self.process_async = True
