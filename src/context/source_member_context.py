from utility.DictEx import DictEx
from .merge_type import MergeType
from .context import Context
from .source_context import SourceContext


class SourceMemberContext(Context):
    """Context for dbSource member request"""

    def __init__(self, sourceContext: SourceContext, member: dict) -> None:
        super().__init__()
        self.__source_context = sourceContext
        self.__member = member
        self.result: list = None
        self.table_name: str = "{0}.{1}".format(
            sourceContext.command.name, member.name)
        self.key_field_name: str = None
        self.status_field_name: str = None
        self.merge_type: MergeType = MergeType.REPLACE

    @property
    def member(self) -> DictEx:
        return self.__member

    @property
    def source_context(self) -> SourceContext:
        return self.__source_context

    @property
    def request(self) -> DictEx:
        return self.source_context.request

    @property
    def command(self) -> DictEx:
        return self.source_context.command
