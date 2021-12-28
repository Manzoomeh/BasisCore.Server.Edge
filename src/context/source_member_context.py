from utility.DictEx import DictEx
from .merge_type import MergeType
from .context import Context
from .source_context import SourceContext


class SourceMemberContext(Context):
    """Context for dbSource member request"""

    def __init__(self, sourceContext: SourceContext, data: list, member: dict) -> None:
        super().__init__(sourceContext.dispatcher,
                         sourceContext.session_id, sourceContext.message_type)
        self.__source_context = sourceContext
        self.__member = member
        self.__data = data
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
    def data(self) -> list:
        return self.__data

    @property
    def cms(self) -> DictEx:
        return self.__source_context.cms

    @property
    def command(self) -> DictEx:
        return self.__source_context.command

    @property
    def url(self) -> str:
        return self.__source_context.url
