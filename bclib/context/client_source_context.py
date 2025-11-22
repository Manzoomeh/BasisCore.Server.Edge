from typing import TYPE_CHECKING

from bclib.context.json_base_request_context import JsonBaseRequestContext
from bclib.parser import HtmlParserEx
from bclib.utility import DictEx

if TYPE_CHECKING:
    from .. import dispatcher, listener


class ClientSourceContext(JsonBaseRequestContext):
    """Context for client dbSource request"""

    def __init__(self, cms_object: dict, dispatcher: 'dispatcher.IDispatcher', message_object: 'listener.SocketMessage') -> None:
        super().__init__(cms_object, dispatcher, message_object)
        parser = HtmlParserEx()
        self.raw_command = self.form.get('command')
        self.dmn_id = self.form.get('dmnid')
        parser.feed(self.raw_command)
        self.command = parser.get_dict()
        self.params: dict = None
        if "params" in self.command:
            params_list = self.command.get('params', [])
            if len(params_list) > 0 and "add" in params_list[0]:
                tmp_dic = {}
                for item in params_list[0].get('add', []):
                    tmp_dic[item.get('name')] = item.get('value')
                self.params = tmp_dic
        self.process_async = True
