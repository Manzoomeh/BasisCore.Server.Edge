from ..db_manager.db import Db
from collections import defaultdict


class MongoDb(Db):
    """Mongo implementation of Db wrapper"""
    client_dict = defaultdict(None)

    def get_instance(self):
        if self.client_dict[self.connection_string] is None:
            MongoDb(self.connection_string)
        self.client = self.client_dict[self.connection_string]
        return self.client

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        import pymongo
        self.connection_string = connection_string
        if self.client_dict[self.connection_string] is not None:
            raise Exception("This class is a singleton!")
        else:
            self.client_dict[self.connection_string] = pymongo.MongoClient(self.connection_string)
            self.client = self.client_dict[self.connection_string]

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self.client.close()
    #     return super().__exit__(exc_type, exc_val, exc_tb)
