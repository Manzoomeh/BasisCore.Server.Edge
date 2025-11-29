import json
from typing import TYPE_CHECKING, Any

from bclib.context.context import Context
from bclib.listener.rabbit.rabbit_message import RabbitMessage

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher


class RabbitContext(Context):
    """Context for rabbit-mq request"""

    def __init__(self, _: dict,  dispatcher: 'IDispatcher', message_object: RabbitMessage) -> None:
        super().__init__(dispatcher, True)
        self.__rabbit_message = message_object
        self.url = self.__rabbit_message.host

    @property
    def host(self) -> 'str':
        return self.__rabbit_message.host

    @property
    def queue(self) -> 'str':
        return self.__rabbit_message.queue

    @property
    def raw_message(self) -> 'str':
        return self.__rabbit_message.message_text

    @property
    def message(self) -> 'RabbitMessage':
        return self.__rabbit_message
