from typing import TYPE_CHECKING

from bclib.context.restful_context import RESTfulContext
from bclib.parser import HtmlParserEx

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher
    from bclib.listener.http.http_message import HttpMessage


class ClientSourceContext(RESTfulContext):
    """Context for client dbSource request"""

    def __init__(self, cms_object: dict, dispatcher: 'IDispatcher', message_object: 'HttpMessage') -> None:
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
