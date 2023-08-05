from bclib.utility import DictEx
from ..time_logger.base_time_logger import BaseTimeLogger
import typing
if typing.TYPE_CHECKING:
    from ..dispatcher.callback_info import CallbackInfo
    from bclib.context import Context
import os

class FileTimeLogger(BaseTimeLogger):
    def __init__(self, options: "DictEx") -> None:
        super().__init__(options)
        if not options.has("file_path"):
            raise KeyError("file_path not found in time logger options!")
        self.__file_path = options.file_path
        if isinstance(self.__file_path, str):
            self.__file_path = [self.__file_path]
        for filepath in self.__file_path:
            path, name = os.path.split(filepath)
            if path != "" and not os.path.isdir(path):
                raise Exception(f"Invalid file path = ${filepath}")

    def _log(self, execution_time: "int", handler: "CallbackInfo", context: "Context"):
        doc = f"FUNCTION {handler.callback_name} EXECUTED IN {execution_time:4d} MILLI SECONDS!"
        for filepath in self.__file_path:
            with open(filepath, "a") as file:
                file.write(f"{doc}\n")
