from .signaler import Signaler


class NoSignaler(Signaler):
    """Implement no signaller for cahce"""

    def __init__(self) -> None:
        super().__init__(None, None)
