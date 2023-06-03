from ..signaler.base_signaler import BaseSignaler

class NoSignaler(BaseSignaler):
    """Implement no signaller for cache"""

    def __init__(self) -> None:
        super().__init__(None, None)