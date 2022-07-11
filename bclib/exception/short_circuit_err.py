class ShortCircuitErr(Exception):
    def __init__(self, status_code: 'str', error_code: 'str' = -1, message: 'str' = None, data: 'dict' = None):
        super().__init__(message if message else '')
        self.data = data
        self.status_code = status_code
        self.error_code = error_code
