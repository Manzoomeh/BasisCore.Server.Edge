from ..exception.not_found_err import NotFoundErr


class HandlerNotFoundErr(NotFoundErr):
    def __init__(self, context_type: str = None):
        super().__init__(f"Suitable handler not found for {context_type}!")
