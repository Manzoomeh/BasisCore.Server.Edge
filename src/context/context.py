from utility import DictEx


class Context():
    """Base class for request context"""

    def __init__(self, request) -> None:
        self.request = DictEx(request)
