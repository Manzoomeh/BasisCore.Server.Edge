from typing import Any
from bclib.context.merge_type import MergeType
from bclib.context.context import Context
from bclib.context.client_source_context import ClientSourceContext

print(__name__)


class ClientSourceMemberContext(Context):
    """Context for dbSource member request"""

    def __init__(self, source_context: 'ClientSourceContext', data: 'Any', member: 'dict') -> None:
        super().__init__(source_context.dispatcher)
        self.__source_context = source_context
        self.member = member
        self.data = data
        self.cms = self.__source_context.cms
        self.command = self.__source_context.command
        self.url = self.__source_context.url
        self.table_name: str = f"{source_context.command.name}.{member.name}"
        self.key_field_name: str = None
        self.status_field_name: str = None
        self.merge_type: MergeType = MergeType.REPLACE
        self.column_names: 'list[str]' = None
