from ..logger.ilogger import ILogger
from ..logger.no_logger import NoLogger
from ..logger.rabbit_schema_base_logger import RabbitSchemaBaseLogger
from ..logger.restful_schema_base_logger import RESTfulSchemaBaseLogger


class LoggerFactory:
    """
    Factory class for creating logger instances based on configuration

    This factory examines the options dictionary and creates the appropriate
    logger type (RESTful, RabbitMQ, or NoLogger) based on the configuration.

    Supported logger types:
        - schema.restful: RESTful API-based logging
        - schema.rabbit: RabbitMQ-based logging
        - None: NoLogger (no logging)

    Example:
        ```python
        options = {
            "logger": {
                "type": "schema.restful",
                "url": "http://logging-service.com/api/logs"
            }
        }
        logger = LoggerFactory.create(options)
        ```
    """

    @staticmethod
    def create(options: dict) -> ILogger:
        """
        Create a logger instance based on configuration

        Args:
            options: Dictionary containing logger configuration with structure:
                {
                    "logger": {
                        "type": "schema.restful" | "schema.rabbit",
                        ... other type-specific options
                    }
                }

        Returns:
            ILogger: Configured logger instance (RESTfulSchemaBaseLogger, 
                    RabbitSchemaBaseLogger, or NoLogger)

        Raises:
            Exception: If logger type is not specified or not supported

        Example:
            ```python
            # RESTful logger
            options = {"logger": {"type": "schema.restful", "url": "..."}}
            logger = LoggerFactory.create(options)

            # RabbitMQ logger
            options = {"logger": {"type": "schema.rabbit", "host": "..."}}
            logger = LoggerFactory.create(options)

            # No logger
            options = {}
            logger = LoggerFactory.create(options)  # Returns NoLogger
            ```
        """
        logger: ILogger = None
        if "logger" not in options:
            logger = NoLogger()
        else:
            logger_option: dict = options.get('logger')
            if 'type' not in logger_option:
                raise Exception("Type property not set for logger!")
            else:
                logger_type = logger_option.get('type').lower()
                if logger_type == 'schema.restful':
                    logger = RESTfulSchemaBaseLogger(logger_option)
                elif logger_type == "schema.rabbit":
                    logger = RabbitSchemaBaseLogger(logger_option)
                else:
                    raise Exception(
                        f"Type '{logger_type}' not support for logger")
            print(f'{logger.__class__.__name__} start logging')
        return logger
