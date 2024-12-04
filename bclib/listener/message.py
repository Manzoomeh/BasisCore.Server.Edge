from typing import Any, Coroutine
from abc import abstractmethod

from bclib.listener.message_type import MessageType


class Message:
    def __init__(self ) -> None:
        self.session_id: str = "not-set"
        self.type: MessageType = MessageType.AD_HOC
    
    @abstractmethod
    async def get_json_async(self)-> Coroutine[Any, Any, dict]:
        pass

    @abstractmethod
    async def set_result_async(self, result: dict)-> Coroutine[Any, Any, None]:
        pass

