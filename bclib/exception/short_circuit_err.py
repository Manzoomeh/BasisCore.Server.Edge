from struct import error
from bclib.utility import HttpStatusCodes


class ShortCircuitErr(error):
    def __init__(self, status_code: HttpStatusCodes, error_code: str = -1, message: str = None):
        super().__init__(message if message else '')
        self.status_code = status_code
        self.error_code = error_code
