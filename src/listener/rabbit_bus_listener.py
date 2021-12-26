import context
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import dispatcher
from .rabbit_listener import RabbitListener
import utility


class RabbitBusListener(RabbitListener):

    def __init__(self, rabbit_options: utility.DictEx,  dispatcher: 'dispatcher.IDispatcher') -> None:
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
                utility.DictEx(message), self.__dispatcher)
            self.__dispatcher.dispatch(new_context)
        except Exception as ex:
            print(
                f"error in dispatcher received message from rabbit in {self._host}:{self._queue_name} ({ex})")
