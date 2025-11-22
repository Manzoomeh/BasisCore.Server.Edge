from abc import ABC, abstractmethod


class IResponseBaseMessage(ABC):
    """Interface for messages that can hold a response"""

    @abstractmethod
    async def set_response_async(self, cms_object: dict) -> None:
        """
        Set the response data for this message

        Args:
            cms_object: The CMS object containing response data
        """
        pass
