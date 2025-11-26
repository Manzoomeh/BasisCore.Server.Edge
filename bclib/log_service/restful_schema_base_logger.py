from bclib.log_service.schema_base_logger import SchemaBaseLogger


class RESTfulSchemaBaseLogger(SchemaBaseLogger):
    """
    RESTful API Schema Logger

    Logger implementation that sends formatted schema data to a RESTful API endpoint.
    Extends SchemaBaseLogger to persist logs via HTTP POST requests.

    Configuration:
        options must contain either:
            - 'url': Direct POST endpoint URL
            - 'post_url': POST endpoint URL
            - 'get_url' or 'url': Schema API URL (inherited from SchemaBaseLogger)

    Example:
        ```python
        options = {
            'url': 'http://api.example.com/schema',
            'post_url': 'http://api.example.com/logs'
        }
        logger = RESTfulSchemaBaseLogger(options)

        log_obj = logger.new_object_log('user_action', user_id=123)
        await logger.log_async(log_obj)
        ```
    """

    def __init__(self, options: dict) -> None:
        """
        Initialize RESTful schema logger

        Args:
            options: Logger configuration dictionary containing:
                - url or post_url: POST endpoint for log submission
                - get_url or url: Schema API endpoint (for parent class)

        Raises:
            Exception: If neither 'url' nor 'post_url' is configured
        """
        super().__init__(options)
        if "url" in options:
            self.__post_url = options["url"]
        elif "post_url" in options:
            self.__post_url = options["post_url"]
        else:
            raise Exception(
                "url part of schema logger not set. set 'url' or 'post_url'")

    async def _save_schema_async(self, schema: dict, routing_key: str = None):
        """
        Save schema data via HTTP POST

        Sends formatted schema data to the configured REST API endpoint.

        Args:
            schema: Formatted schema data to send
            routing_key: Ignored for RESTful logger

        Raises:
            Exception: If HTTP response status is not 200
            aiohttp exceptions: If network request fails
        """
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(self.__post_url, json={"schema": schema}) as response:
                if response.status != 200:
                    raise Exception(
                        f"Error in send answer schema to server.(status code ={response.status}) :{await response.text()}")
