import pymongo
from ..db_manager.db import Db


class MongoDb(Db):
    """Mongo implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        self.client = pymongo.MongoClient(connection_string)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
        return super().__exit__(exc_type, exc_val, exc_tb)
