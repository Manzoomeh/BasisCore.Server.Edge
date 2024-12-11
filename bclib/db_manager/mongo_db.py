class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `_init_` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class MongoDb(metaclass=SingletonMeta):
    """Mongo implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        import pymongo
        self.client = pymongo.MongoClient(connection_string)

    # def _exit_(self, exc_type, exc_val, exc_tb):
    #     self.client.close()
    #     return super()._exit_(exc_type, exc_val, exc_tb)
