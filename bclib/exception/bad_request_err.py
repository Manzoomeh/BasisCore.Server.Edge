from bclib.utility.http_status_codes import HttpStatusCodes
from bclib.exception.short_circuit_err import ShortCircuitErr


class BadRequestErr(ShortCircuitErr):
    def __init__(self, message: str = None, data: 'dict' = None):
        super().__init__(HttpStatusCodes.BAD_REQUEST, 'http-400', message, data)
