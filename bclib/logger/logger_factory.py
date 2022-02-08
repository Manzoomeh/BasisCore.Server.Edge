from ..logger.no_logger import NoLogger
from ..logger.schema_base_logger import SchemaBaseLogger
from bclib.utility import DictEx
from ..logger.ilogger import ILogger


class LoggerFactory:

    @staticmethod
    def create(options: DictEx) -> ILogger:
        logger: ILogger = None
        if not options.has("logger"):
            logger = NoLogger()
        else:
            logger_option: DictEx = options.logger
            if not logger_option.has('type'):
                raise Exception("Type property not set for logger!")
            else:
                logger_type = logger_option.type
                if logger_type == 'schema':
                    logger = SchemaBaseLogger(logger_option)
                else:
                    raise Exception(
                        f"Type '{logger_type}' not support for logger")

        return logger
