"""RESTful implementation of Db wrapper"""
from typing import Any
import requests
from ..db_manager.db import Db


class RESTfulConnection(Db):
    """RESTful implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        self.__api_url = connection_string

    def get(self, segment: str = None, params: dict = None) -> Any:
        """Send get request to web api"""

        url = self.__api_url if segment is None else '{0}{1}'.format(
            self.__api_url, segment)

        response = requests.get(url, params=params)
        return response.json()

    def post(self, segment: str = None, params: dict = None) -> Any:
        """Send post request to web api"""

        url = self.__api_url if segment is None else '{0}{1}'.format(
            self.__api_url, segment)
        response = requests.post(url, data=params)
        return response.json()
