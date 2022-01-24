from abc import ABC, abstractmethod
from typing import Any

from ..context.merge_type import MergeType

from bclib.utility import DictEx


class SourceMemberContext(ABC):

    @property
    @abstractmethod
    def member(self) -> DictEx:
        pass

    @property
    @abstractmethod
    def data(self) -> Any:
        pass

    @property
    @abstractmethod
    def command(self) -> DictEx:
        pass

    @property
    @abstractmethod
    def table_name(self) -> str:
        pass

    @property
    @abstractmethod
    def key_field_name(self) -> str:
        pass

    @property
    @abstractmethod
    def status_field_name(self) -> str:
        pass

    @property
    @abstractmethod
    def merge_type(self) -> MergeType:
        pass
