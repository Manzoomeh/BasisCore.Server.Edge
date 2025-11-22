"""CMS Base Message - Base class for messages with CMS object support"""
from abc import ABC, abstractmethod
from typing import Any, Optional

from bclib.listener.message import Message


class CmsBaseMessage(Message):
    """
    Base class for messages that contain CMS objects

    This abstract base class provides a common interface for all messages
    that work with CMS (Content Management System) objects, including
    HTTP, Socket, and WebSocket messages.

    Subclasses must implement the cms_object property to provide access
    to their CMS data structure.
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

    @abstractmethod
    def set_response(self, response_data: Any) -> None:
        """
        Set response data in this message

        Args:
            response_data: The response data to set
        """
        pass
