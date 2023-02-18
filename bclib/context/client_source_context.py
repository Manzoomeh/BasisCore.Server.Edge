from typing import TYPE_CHECKING

from bclib.parser import HtmlParserEx
from bclib.utility import DictEx
from bclib.context.json_base_request_context import JsonBaseRequestContext

if TYPE_CHECKING:
    from .. import dispatcher


class ClientSourceContext(JsonBaseRequestContext):
    """Context for client dbSource request"""

    def __init__(self, cms_object: dict, dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(cms_object, dispatcher)
        parser = HtmlParserEx()
        self.raw_command = self.cms.form.command
        self.dmn_id = self.cms.form.dmnid if self.cms.form.has(
            'dmnid') else None
        parser.feed(self.raw_command)
        self.command = parser.get_dict_ex()
        self.params: DictEx = None
        if "params" in self.command:
            if len(self.command.params) > 0 and "add" in self.command.params[0]:
                tmp_dic = dict()
                for item in self.command.params[0].add:
                    tmp_dic[item.name] = item.value
                self.params = DictEx(tmp_dic)
        self.process_async = True
