import enum


class MessageType(enum.Enum):
    CONNECT = 1
    MESSAGE = 2
    DISCONNECT = 3
    AD_HOC = 4
    NOT_EXIST = 5
