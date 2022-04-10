from abc import ABC, abstractmethod
from bclib.db_manager import DbManager
from bclib import edge


class IDbManager(ABC):

    @abstractmethod
    def open_sql_connection(self, key: str):
        pass

    @abstractmethod
    def open_sqllite_connection(self, key: str):
        pass

    @abstractmethod
    def open_mongo_connection(self, key: str):
        pass

    @abstractmethod
    def open_restful_connection(self, key: str):
        pass

    @abstractmethod
    def open_rabbit_connection(self, key: str):
        pass


class EdgeDbManager(IDbManager):
    def __init__(self, provider: DbManager) -> None:
        super().__init__()
        self.provider = provider

    def open_sql_connection(self, key: str):
        return self.provider.open_sql_connection(key)

    def open_sqllite_connection(self, key: str):
        return self.provider.open_sqllite_connection(key)

    def open_mongo_connection(self, key: str):
        return self.provider.open_mongo_connection(key)

    def open_restful_connection(self, key: str):
        return self.provider.open_restful_connection(key)

    def open_rabbit_connection(self, key: str):
        return self.provider.open_rabbit_connection(key)


class TestDbManager(EdgeDbManager):

    def __init__(self, options: edge.DictEx) -> None:
        super().__init__(DbManager(options))
