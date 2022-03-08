from abc import abstractmethod
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

    async def __load_schema_async(self, schema_id: int) -> LogSchema:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(self.__get_url, params={"schemaId": schema_id}) as response:
                return LogSchema(await response.json())

    @abstractmethod
    async def _save_schema_async(self, schema: dict):
        """Save scheme async"""

    async def __get_dict_async(self, schema_id: int) -> LogSchema:
        if schema_id not in self.__schemas:
            schema = await self.__load_schema_async(schema_id)
            self.__schemas[schema.schema_id] = schema
        return self.__schemas[schema_id]

    async def log_async(self,  **kwargs):
        """log data async"""
        try:
            if 'schema_id' in kwargs:
                schema_id = kwargs["schema_id"]
                questions = await self.__get_dict_async(schema_id)
                answer = questions.get_answer(kwargs)
                await self._save_schema_async(answer)
            else:
                raise Exception("'schema_id' not set for apply logging!")
        except Exception as ex:
            print(
                f"Error in log with schema logger: {repr(ex)}")
