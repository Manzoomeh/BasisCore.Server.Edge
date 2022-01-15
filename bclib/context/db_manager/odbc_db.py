"""
Implementation of ODBC base Db object
https://github.com/mkleehammer/pyodbc/wiki
"""
from ..db_manager.db import Db


class OdbcDb(Db):
    """Implementation of ODBC base Db object"""

    def __init__(self, connection_string: str) -> None:
        super().__init__()
        import pyodbc
        self.connection = pyodbc.connect(connection_string)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connection.close()
        return super().__exit__(exc_type, exc_val, exc_tb)
