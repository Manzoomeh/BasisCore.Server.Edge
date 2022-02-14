from ..logger.schema_base_logger import SchemaBaseLogger
from bclib.utility import DictEx


class RESTfulSchemaBaseLogger(SchemaBaseLogger):
    def __init__(self, options: DictEx) -> None:
        super().__init__(options)
        if options.has("url"):
            self.__post_url = options.url
        elif options.has("post_url"):
            self.__post_url = options.post_url
        else:
            raise Exception(
                "url part of schema logger not set. set 'url' or 'post_url'")

    async def _save_schema_async(self, schema: dict):
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(self.__post_url, json={"schema": schema}) as response:
                if response.status != 200:
                    raise Exception(
                        f"Error in send answer schema to server.(status code ={response.status}) :{await response.text()}")
