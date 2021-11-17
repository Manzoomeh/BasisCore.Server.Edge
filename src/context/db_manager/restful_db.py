"""RESTful implementation of Db wrapper"""
from typing import Any
import requests
from .db import Db


class RESTful(Db):
    """RESTful implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        self.__api_url = connection_string

    def get(self) -> Any:
        """Send get request to web api"""
        response = requests.get(self.__api_url)
        return response.json()

    def post(self, data: Any) -> Any:
        """Send post request to web api"""
        response = requests.post(self.__api_url, json=data)
        return response.json()
