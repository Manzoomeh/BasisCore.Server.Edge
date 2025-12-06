"""ICmsBaseMessage - Interface for messages with CMS object support"""
from abc import ABC, abstractmethod


class ICmsBaseMessage(ABC):
    """
    Interface for messages that contain CMS objects

    This abstract base class provides a common interface for all messages
    that work with CMS (Content Management System) objects, including
    HTTP, Socket, and WebSocket messages.

    Implementations must provide the cms_object property to expose their
    CMS data structure as a dictionary.

    The 'I' prefix indicates this is an interface that defines the contract
    for CMS-aware message types.

    Example:
        ```python
        class MyMessage(Message, ICmsBaseMessage):
            def __init__(self, data: dict):
                self._data = data

            @property
            def cms_object(self) -> dict:
                return self._data.get('cms', {})
        ```
    """

    @property
    @abstractmethod
    def cms_object(self) -> dict:
        """
        Get the CMS object for this message

        Returns:
            dict: The CMS object containing message data and metadata
        """
        pass
