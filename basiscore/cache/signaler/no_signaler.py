from ..signaler.signaler_base import SignalerBase


class NoSignaler(SignalerBase):
    """Implement no signaller for cache"""

    def __init__(self) -> None:
        super().__init__(None, None)
