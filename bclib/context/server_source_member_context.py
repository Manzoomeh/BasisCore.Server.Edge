from typing import Any, TYPE_CHECKING, Optional
from bclib.context.merge_type import MergeType
from bclib.context.context import Context
if TYPE_CHECKING:
    from bclib.context.server_source_context import ServerSourceContext


class ServerSourceMemberContext(Context):
    """Context for Server dbSource member request"""

    def __init__(self, source_context: 'ServerSourceContext', data: Any, member: 'dict') -> None:
        super().__init__(source_context.dispatcher)
        self.__source_context = source_context
        self.member = member
        self.data = data
        self.command = self.__source_context.command
        self.table_name: str = f"{source_context.command.name}.{member.name}"
        self.key_field_name: Optional[str] = None
        self.status_field_name: Optional[str] = None
        self.merge_type: MergeType = MergeType.REPLACE
        self.column_names: 'list[str]' = None
