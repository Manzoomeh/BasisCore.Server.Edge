from aiohttp import web

from bclib.listener.message import Message
from bclib.listener.message_type import MessageType


class WebMessage(Message):
    """Message specialization for HTTP (dev server) flow.

    Holds the parsed cms_object directly to avoid JSON serialize/deserialize
    overhead when running inside the in-process development edge server.
    """

    def __init__(self, session_id: str, message_type: MessageType, cms_object: dict):
        # We deliberately do NOT serialize cms_object into buffer.
        super().__init__(session_id, message_type, buffer=None)
        self.cms_object = cms_object  # keep local

    def create_response_message(self, session_id: str, cms_object: dict) -> "Message":
        self.cms_object = cms_object  # update local cms_object
        return self
