from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from listener.message import Message


class IMessageHandler(ABC):
    """Interface for message handler classes"""

    @abstractmethod
    async def on_message_receive_async(self, message: 'Message') -> None:
        """Process received message and dispatch to appropriate handler

        This is the main entry point for listeners to send messages to the dispatcher.
        The method processes the message, dispatches it to the appropriate handler,
        and sets the response on the message object if it implements IResponseBaseMessage.

        Args:
            message: The message to process

        Note:
            This method does not return anything. For messages that implement
            IResponseBaseMessage, the response is set directly on the message object
            via message.set_response_async().
        """
        pass
