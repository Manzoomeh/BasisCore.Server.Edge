from ..db_manager.db import Db
from collections import defaultdict


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def _call_(cls, *args, **kwargs):
        """
        Possible changes to the value of the `_init_` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super()._call_(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class MongoDb(metaclass=SingletonMeta):
    """Mongo implementation of Db wrapper"""
    client_dict = defaultdict(None)

    def _init_(self, connection_string: str) -> None:
        super()._init_()
        import pymongo
        self.client = pymongo.MongoClient(connection_string)

    # def _exit_(self, exc_type, exc_val, exc_tb):
    #     self.client.close()
    #     return super()._exit_(exc_type, exc_val, exc_tb)
