from typing import Any, TypeVar

from bclib.utility import resolve_dict_value

from .app_options import AppOptions
from .ioptions import IOptions

T = TypeVar('T')


class ServiceOptions(IOptions[T]):
    """
    Options Implementation

    Concrete implementation of IOptions interface.
    Resolves configuration values from AppOptions dictionary.
    """

    def __init__(self, value: dict | None = None):
        if value:
            super().__init__(value)
        else:
            super().__init__()
