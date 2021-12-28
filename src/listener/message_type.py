import enum


class MessageType(enum.Enum):
    connect = 1
    message = 2
    disconnect = 3
    ad_hock = 4
