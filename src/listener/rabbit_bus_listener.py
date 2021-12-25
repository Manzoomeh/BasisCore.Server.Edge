from typing import Callable
from context import Context, RabbitContext
from listener.rabbit_listener import RabbitListener
from utility import DictEx


class RabbitBusListener(RabbitListener):

    def __init__(self, rabbit_options: DictEx, host_options: DictEx, dispatcher: Callable[[Context], any]) -> None:
        super().__init__(rabbit_options)
        self._host_options = host_options
        self._dispatcher = dispatcher

    def on_rabbit_message_received(self, body):
        try:
            message = {
                "host": self._host,
                "queue": self._queue_name,
                "message":  body.decode("utf-8")
            }
            context = RabbitContext(DictEx(message), self._host_options)
            self._dispatcher(context)
        except Exception as ex:
            print(
                f"error in dispatcher received message from rabbit in {self._host}:{self._queue_name} ({ex})")
