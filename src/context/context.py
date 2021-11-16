from .db_manager import DbManager, SqlDb, SQLiteDb, MongoDb


class Context:
    """Base class for dispatching"""

    def __init__(self, options: dict) -> None:
        self._options = options
        self.__db_manager = DbManager(options)

    def open_sql_connection(self, key: str) -> SqlDb:
        return self.__db_manager.open_sql_connection(key)

    def open_sqllite_connection(self, key: str) -> SQLiteDb:
        return self.__db_manager.open_sqllite_connection(key)

    def open_mongo_connection(self, key: str) -> MongoDb:
        return self.__db_manager.open_mongo_connection(key)

    def open_restful_connection(self, key: str) -> MongoDb:
        return self.__db_manager.open_restful_connection(key)
