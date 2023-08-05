from bclib.utility import DictEx
from ..time_logger.base_time_logger import BaseTimeLogger
import typing
if typing.TYPE_CHECKING:
    from ..dispatcher.callback_info import CallbackInfo
    from bclib.context import Context

class ConsoleTimeLogger(BaseTimeLogger):
    def __init__(self, options: DictEx) -> None:
        super().__init__(options)

    def _log(self, execution_time: "float", handler: "CallbackInfo", context: "Context"):
        print(f"FUNCTION {handler.callback_name} EXECUTED IN {execution_time:4d} MILLI SECONDS!")
    # def log(self, execution_time: "float", handler: "CallbackInfo", context:"Context"):
    #     print(f"FUNCTION {handler.callback_name} EXECUTED IN {int(execution_time * 1000):4d} MILLI SECONDS!")