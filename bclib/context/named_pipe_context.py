from typing import TYPE_CHECKING
from . import Context
if TYPE_CHECKING:
    from .. import dispatcher
from bclib.utility import DictEx


class NamedPipeContext(Context):
    """Context for named pipe request"""

    def __init__(self, named_pipe_message: 'dict', raw_message: str, dispatcher: 'dispatcher.IDispatcher'):
        super().__init__(dispatcher)
        self.message: DictEx = DictEx(named_pipe_message)
        self.raw_message = raw_message
