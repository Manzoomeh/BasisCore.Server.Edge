from abc import ABC, abstractmethod
from bclib.utility import DictEx
import typing
if typing.TYPE_CHECKING:
    from ..dispatcher.callback_info import CallbackInfo
    from bclib.context import Context

class BaseTimeLogger(ABC):
    def __init__(self, options:"DictEx") -> None:
        super().__init__()
        self._options = options
        self._critical_time = float(options.critical_time) if options.has("critical_time") else 0

    @abstractmethod
    def _log(self, execution_time:"int", handler:"CallbackInfo", context:"Context"):
        raise Exception("This method not implemented!")
    
    def log(self, execution_time:"float", handler:"CallbackInfo", context:"Context"):
        execution_time = int(execution_time * 1000)
        if execution_time >= self._critical_time:
            self._log(execution_time, handler, context)