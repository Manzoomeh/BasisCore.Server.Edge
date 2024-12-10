from typing import Optional
from bclib.utility import DictEx
from bclib.logger.rabbit_schema_base_logger import RabbitSchemaBaseLogger
from bclib.logger.restful_schema_base_logger import RESTfulSchemaBaseLogger
from bclib.logger.no_logger import NoLogger
from bclib.logger.ilogger import ILogger


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
                    logger = RESTfulSchemaBaseLogger(options)
                elif logger_type == "schema.rabbit":
                    logger = RabbitSchemaBaseLogger(options)
                else:
                    raise Exception(
                        f"Type '{logger_type}' not support for logger")
        return logger
