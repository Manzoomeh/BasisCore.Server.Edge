from typing import Any
from .db import Db
import requests


class RESTful(Db):
    """Restful implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        self.__api_url = connection_string

    def __exit__(self, exc_type, exc_val, exc_tb):
        return super().__exit__(exc_type, exc_val, exc_tb)

    def get(self) -> Any:
        response = requests.get(self.__api_url)
        return response.json()

    def post(self, data: Any) -> Any:
        response = requests.post(self.__api_url, json=data)
        return response.json()
