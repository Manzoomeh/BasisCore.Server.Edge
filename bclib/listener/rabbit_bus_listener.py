from struct import error
from typing import TYPE_CHECKING

from bclib.listener.rabbit_listener import RabbitListener
from bclib.utility import DictEx

if TYPE_CHECKING:
    from .. import dispatcher


class RabbitBusListener(RabbitListener):

    def __init__(self, rabbit_options: DictEx,  dispatcher: 'dispatcher.IDispatcher') -> None:
        # RabbitBusListener handles messages directly via dispatcher, not through callback
        # Pass a dummy callback to satisfy IListener interface
        async def _dummy_callback(msg):
            return None
        super().__init__(rabbit_options, _dummy_callback)
        self.__dispatcher = dispatcher

    def on_rabbit_message_received(self, body):
        try:
            # Lazy import to avoid circular dependency
            from bclib.context import RabbitContext

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
