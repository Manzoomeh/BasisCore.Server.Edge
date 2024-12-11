from struct import error
from typing import TYPE_CHECKING
from bclib.context.rabbit_context import RabbitContext
from bclib.listener.rabbit_listener import RabbitListener
from bclib.utility.dict_ex import DictEx

if TYPE_CHECKING:
    from bclib.dispatcher import IDispatcher


class RabbitBusListener(RabbitListener):

    def __init__(self, rabbit_options: 'DictEx',  dispatcher: 'IDispatcher') -> None:
        super().__init__(rabbit_options)
        self.__dispatcher = dispatcher

    def on_rabbit_message_received(self, body):
        try:
            message = {
                "host": self._host,
                "queue": self._queue_name,
                "message":  body.decode("utf-8")
            }
            new_context = RabbitContext(
                DictEx(message), self.__dispatcher)
            self.__dispatcher.dispatch_in_background(new_context)
        except error as ex:
            print(
                f"error in dispatcher received message from rabbit in {self._host}:{self._queue_name} ({ex})")
