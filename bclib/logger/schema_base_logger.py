from abc import abstractmethod
from urllib.parse import urljoin
from bclib.logger.log_object import LogObject
from bclib.utility import DictEx

from ..logger.log_schema import LogSchema
from ..logger.ilogger import ILogger


class SchemaBaseLogger(ILogger):

    def __init__(self, options: DictEx) -> None:
        super().__init__()
        self.options = options
        if options.has("url"):
            self.__get_url = options.url
        elif options.has("get_url"):
            self.__get_url = options.get_url
        else:
            raise Exception(
                "url part of schema logger not set. set 'url' or 'get_url'")
        self.__schemas: 'dict[str,dict]' = dict()

    async def __load_schema_async(self, schema_name: str) -> LogSchema:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            url = urljoin(self.__get_url+"/", schema_name)
            async with session.get(url) as response:
                schema_source = await response.json()
                return LogSchema(schema_source["sources"][0]["data"][0])

    @abstractmethod
    async def _save_schema_async(self, schema: dict):
        """Save scheme async"""

    async def __get_dict_async(self, schema_name: int) -> LogSchema:
        if schema_name not in self.__schemas:
            schema = await self.__load_schema_async(schema_name)
            self.__schemas[schema_name] = schema
        return self.__schemas[schema_name]

    async def log_async(self, log_object: LogObject):
        """log data async"""
        try:
            questions = await self.__get_dict_async(
                schema_name=log_object.schema_name
            )
            answer = questions.get_answer(
                params=log_object.properties
            )
            await self._save_schema_async(answer)
        except Exception as ex:
            print(
                f"Error in log with schema logger: {repr(ex)}")
