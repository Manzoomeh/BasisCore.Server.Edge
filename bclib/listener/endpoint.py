class Endpoint:
    """Represent ip and port number for endpoint"""

    def __init__(self, url: str):
        parts = url.split(':')
        self.__url = parts[0]
        self.__port = int(parts[1]) if len(parts) >= 2 else 80

    @property
    def url(self) -> str:
        return self.__url

    @property
    def port(self) -> int:
        return self.__port
