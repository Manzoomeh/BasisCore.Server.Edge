"""Base class for implement data base interface"""
from abc import ABC


class Db(ABC):
    """Base class for implement data base interface"""

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
