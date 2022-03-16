from abc import ABC
from typing import Any
from .merge_type import MergeType
from .context import Context
from .client_source_context import ClientSourceContext


class ClientSourceMemberContext(Context):
    """Context for dbSource member request"""

    def __init__(self, sourceContext: ClientSourceContext, data: Any, member: dict) -> None:
        super().__init__(sourceContext.dispatcher)
        self.__source_context = sourceContext
        self.member = member
        self.data = data
        self.cms = self.__source_context.cms
        self.command = self.__source_context.command
        self.url = self.__source_context.url
        self.table_name: str = f"{sourceContext.command.name}.{member.name}"
        self.key_field_name: str = None
        self.status_field_name: str = None
        self.merge_type: MergeType = MergeType.REPLACE
        self.column_names: 'list[str]' = None
