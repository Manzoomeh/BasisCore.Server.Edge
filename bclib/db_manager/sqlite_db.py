import sqlite3
from bclib.db_manager.db import Db


class SQLiteDb(Db):
    """SQLite implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        self.connection = sqlite3.connect(connection_string)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
        return super().__exit__(exc_type, exc_val, exc_tb)
