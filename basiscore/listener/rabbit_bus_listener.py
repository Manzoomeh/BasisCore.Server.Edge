from struct import error
import context
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .. import dispatcher
from ..listener.rabbit_listener import RabbitListener
from basiscore.utility import DictEx


class RabbitBusListener(RabbitListener):

    def __init__(self, rabbit_options: DictEx,  dispatcher: 'dispatcher.IDispatcher') -> None:
        super().__init__(rabbit_options)
        self.__dispatcher = dispatcher

    def on_rabbit_message_received(self, body):
        try:
            message = {
                "host": self._host,
                "queue": self._queue_name,
                "message":  body.decode("utf-8")
            }
            new_context = context.RabbitContext(
                DictEx(message), self.__dispatcher)
            self.__dispatcher.dispatch(new_context)
        except error as ex:
            print(
                f"error in dispatcher received message from rabbit in {self._host}:{self._queue_name} ({ex})")
