from typing import Optional
from bclib.utility import DictEx
from .rabbit_schema_base_logger import RabbitSchemaBaseLogger
from .restful_schema_base_logger import RESTfulSchemaBaseLogger
from .no_logger import NoLogger
from .ilogger import ILogger


class LoggerFactory:

    @staticmethod
    def create(options: DictEx) -> ILogger:
        logger: Optional[ILogger] = None
        if not options.has("logger"):
            logger = NoLogger(options)
        else:
            logger_option: DictEx = options.logger
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
        return logger
