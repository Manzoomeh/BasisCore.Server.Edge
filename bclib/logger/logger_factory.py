from bclib.utility import DictEx
from ..logger.rabbit_schema_base_logger import RabbitSchemaBaseLogger
from ..logger.restful_schema_base_logger import RESTfulSchemaBaseLogger
from ..logger.no_logger import NoLogger
from ..logger.ilogger import ILogger


class LoggerFactory:

    @staticmethod
    def create(options: DictEx) -> "list[ILogger]|ILogger":
        logger: "ILogger|list[ILogger]" = None
        if not options.has("logger"):
            logger = NoLogger(options)
        else:
            loggers_option: "list[DictEx]|DictEx" = options.logger
            if not isinstance(loggers_option, list):
                logger = LoggerFactory.apply_logger(loggers_option)
            else:
                logger = list()
                for logger_option in loggers_option:
                    if not logger_option.has("name"):
                        raise Exception("logger must be has a name!")
                    logger.append(LoggerFactory.apply_logger(logger_option))
        return logger

    @staticmethod
    def apply_logger(logger_option: DictEx) -> "ILogger":
        if not logger_option.has('type'):
            raise Exception("Type property not set for logger!")
        else:
            logger_type = logger_option.type.lower()
            if logger_type == 'schema.restful':
                logger = RESTfulSchemaBaseLogger(logger_option)
            elif logger_type == "schema.rabbit":
                logger = RabbitSchemaBaseLogger(logger_option)
            else:
                raise Exception(
                    f"Type '{logger_type}' not support for logger")
        print(f'{logger.__class__.__name__} start logging')
        return logger