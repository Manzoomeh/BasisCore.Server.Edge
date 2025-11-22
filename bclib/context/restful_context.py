import json
from typing import TYPE_CHECKING
from urllib.parse import parse_qsl

from bclib.utility import DictEx

from ..context.json_base_request_context import JsonBaseRequestContext

if TYPE_CHECKING:
    from .. import dispatcher, listener


class RESTfulContext(JsonBaseRequestContext):
    def __init__(self, cms_object: dict, dispatcher: 'dispatcher.IDispatcher', message_object: 'listener.SocketMessage') -> None:
        super().__init__(cms_object, dispatcher, message_object)
        temp_data = None
        if self.form:
            temp_data = self.form
        else:
            request = self.cms.get('request', {})
            body = request.get('body')
            if body:
                content_type = request.get('content-type')
                if content_type and content_type.find("x-www-form-urlencoded") > -1:
                    temp_data = dict()
                    for key, value in parse_qsl(body):
                        temp_data[key.strip()] = value
                elif content_type and content_type.find("json") > -1:
                    try:
                        temp_data = json.loads(body)
                    except Exception as ex:
                        print('error in extract request body', ex)
        self.body = temp_data
