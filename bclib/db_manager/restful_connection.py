"""RESTful implementation of Db wrapper"""
from typing import Any
from ..db_manager.db import Db


class RESTfulConnection(Db):
    """RESTful implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        self.__api_url = connection_string

    async def get_async(self, segment: str = None, params: dict = None) -> Any:
        """Send get request to web api"""

        url = self.__api_url if segment is None else '{0}{1}'.format(
            self.__api_url, segment)
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    async def post_async(self, segment: str = None, params: dict = None) -> Any:
        """Send post request to web api"""

        url = self.__api_url if segment is None else '{0}{1}'.format(
            self.__api_url, segment)
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as response:
                return await response.json()
