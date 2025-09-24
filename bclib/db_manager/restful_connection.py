"""RESTful implementation of Db wrapper"""
from typing import Any
from bclib.db_manager.db import Db


class RESTfulConnection(Db):
    """RESTful implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        self.__api_url = connection_string

    async def get_async(self, segment: str = None, params: dict = None, pre_segment: str = None) -> Any:
        """Send get request to web api"""

        url = self.__api_url if segment is None else '{0}{1}'.format(
            self.__api_url, segment)
        if pre_segment:
            url = '{0}{1}'.format(pre_segment, url)
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                return await response.json()

    async def post_async(self, segment: str = None, params: dict = None, pre_segment: str = None) -> Any:
        """Send post request to web api"""

        url = self.__api_url if segment is None else '{0}{1}'.format(
            self.__api_url, segment)
        if pre_segment:
            url = '{0}{1}'.format(pre_segment, url)
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=params) as response:
                return await response.json()
