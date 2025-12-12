class Endpoint:
    """Represent ip and port number for endpoint"""

    def __init__(self, host: str, port: int = 80):
        parts = host.split(':')
        self.__host = parts[0]
        self.__port = int(parts[1]) if len(parts) >= 2 else port

    @property
    def host(self) -> str:
        return self.__host

    @property
    def port(self) -> int:
        return self.__port
