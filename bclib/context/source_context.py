from abc import ABC, abstractmethod
from bclib.utility.dict_ex import DictEx


class SourceContext(ABC):
    """Base class for manage source base context"""

    @property
    @abstractmethod
    def raw_command(self) -> str:
        pass

    @property
    @abstractmethod
    def command(self) -> DictEx:
        pass

    @property
    @abstractmethod
    def params(self) -> DictEx:
        pass

    @property
    @abstractmethod
    def dmn_id(self) -> int:
        pass

    @property
    @abstractmethod
    def process_async(self) -> bool:
        pass
