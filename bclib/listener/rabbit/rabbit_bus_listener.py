from struct import error
from typing import TYPE_CHECKING

from bclib.listener.rabbit.rabbit_listener import RabbitListener
from bclib.listener.rabbit.rabbit_message import RabbitMessage
from bclib.utility import DictEx

if TYPE_CHECKING:
    from bclib import dispatcher


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
            # Create RabbitMessage with host, queue, and message body
            message = RabbitMessage(
                host=self._host,
                queue=self._queue_name,
                body=body,
                routing_key=self._routing_key if hasattr(
                    self, '_routing_key') else None
            )

            # Lazy import to avoid circular dependency
            from bclib.context import RabbitContext

            # Create legacy DictEx for backward compatibility with RabbitContext
            legacy_message = {
                "host": message.host,
                "queue": message.queue,
                "message": message.message_text
            }
            new_context = RabbitContext(
                DictEx(legacy_message), self.__dispatcher)
            self.__dispatcher.dispatch_in_background(new_context)
        except error as ex:
            print(
                f"error in dispatcher received message from rabbit in {self._host}:{self._queue_name} ({ex})")
