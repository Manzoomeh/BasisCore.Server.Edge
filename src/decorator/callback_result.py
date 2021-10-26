class CallbackResult:
    def __init__(self, result) -> None:
        self.processed = True if result is None else False
