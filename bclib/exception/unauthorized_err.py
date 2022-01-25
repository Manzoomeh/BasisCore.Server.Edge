from bclib.utility.http_status_codes import HttpStatusCodes
from ..exception.short_circuit_err import ShortCircuitErr


class UnauthorizedErr(ShortCircuitErr):
    def __init__(self, message: str = None):
        super().__init__(HttpStatusCodes.UNAUTHORIZED, 'http-401', message)
