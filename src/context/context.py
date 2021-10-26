from utility import DictEx


class Context():
    """Base class for request context"""

    def __init__(self, request) -> None:
        self.__request = DictEx(request)

    @property
    def request(self) -> DictEx:
        return self.__request
