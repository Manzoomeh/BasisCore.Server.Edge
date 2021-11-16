from .odbc_db import OdbcDb


class SqlDb(OdbcDb):
    """SqlServer implementation of Db wrapper"""

    def __init__(self, connection_string: str) -> None:
        super().__init__(connection_string)
