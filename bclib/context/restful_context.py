import json
from typing import TYPE_CHECKING
from urllib.parse import parse_qsl

from bclib.utility import DictEx

from ..context.json_base_request_context import JsonBaseRequestContext

if TYPE_CHECKING:
    from .. import dispatcher, listener


class RESTfulContext(JsonBaseRequestContext):
    def __init__(self, cms_object: dict, dispatcher: 'dispatcher.IDispatcher', message_object: 'listener.WebMessage') -> None:
        super().__init__(cms_object, dispatcher, message_object)
        temp_data = None
        if self.cms.form:
            temp_data = self.cms.form
        else:
            body = self.cms.request.body
            if body:
                content_type = self.cms.request.get("content-type")
                if content_type.find("x-www-form-urlencoded") > -1:
                    temp_data = dict()
                    for key, value in parse_qsl(body):
                        temp_data[key.strip()] = value
                elif content_type.find("json") > -1:
                    try:
                        temp_data = json.loads(self.cms.request.body)
                    except Exception as ex:
                        print('error in extract request body', ex)
        self.body = DictEx(temp_data) if temp_data else None
