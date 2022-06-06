from abc import ABC, abstractmethod
from typing import Any


class INamedPipeConnection(ABC):

    @abstractmethod
    def try_send_command(self, command: 'Any') -> bool:
        pass

    @abstractmethod
    async def try_send_query_async(self, query: 'Any') -> 'Any':
        pass
