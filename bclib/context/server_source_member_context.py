from typing import Any
from ..context.merge_type import MergeType
from ..context.context import Context
from ..context.server_source_context import ServerSourceContext


class ServerSourceMemberContext(Context):
    """Context for Server dbSource member request"""

    def __init__(self, sourceContext: ServerSourceContext, data: Any, member: dict) -> None:
        super().__init__(sourceContext.dispatcher)
        self.__source_context = sourceContext
        self.member = member
        self.data = data
        self.command = self.__source_context.command
        self.table_name: str = f"{sourceContext.command.name}.{member.name}"
        self.key_field_name: str = None
        self.status_field_name: str = None
        self.merge_type: MergeType = MergeType.REPLACE
        self.column_names: 'list[str]' = None
