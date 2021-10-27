class EndPoint:
    """Represent ip and port number for endpoint"""

    def __init__(self, url: str, port: int):
        self.__url = url
        self.__port = port

    @property
    def url(self) -> str:
        return self.__url

    @property
    def port(self) -> int:
        return self.__port
