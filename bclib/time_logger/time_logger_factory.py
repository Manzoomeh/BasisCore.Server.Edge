from bclib.utility import DictEx
from ..time_logger.base_time_logger import BaseTimeLogger
from ..time_logger.no_time_logger import NoTimeLogger
from ..time_logger.file_time_logger import FileTimeLogger
from ..time_logger.rabbit_time_logger import RabbitTimeLogger
from ..time_logger.udp_time_logger import UDPTimeLogger
from ..time_logger.console_time_logger import ConsoleTimeLogger

class TimeLoggerFactory:

    @staticmethod
    def create(options: "DictEx") -> "BaseTimeLogger":
        logger: "BaseTimeLogger" = None
        if not options.has("time_logger"):
            logger = NoTimeLogger(options=None)
        else:
            time_logger_option: "DictEx" = options.time_logger
            if not time_logger_option.has('type'):
                raise Exception("Type property not set for time logger!")
            else:
                logger_type = time_logger_option.type.lower()
                if logger_type == "udp":
                    logger = UDPTimeLogger(time_logger_option)
                elif logger_type == "console":
                    logger = ConsoleTimeLogger(time_logger_option)
                elif logger_type == 'rabbit':
                    logger = RabbitTimeLogger(time_logger_option)
                elif logger_type == "file":
                    logger = FileTimeLogger(time_logger_option)
                else:
                    raise Exception(
                        f"Type ${logger_type} not support for logger")
            print(f'{logger.__class__.__name__} start logging for time!')

        return logger
