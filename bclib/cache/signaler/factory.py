from abc import ABC
from ..signaler.base_signaler import BaseSignaler
from bclib.utility import DictEx
from ..signaler.time_signaler import TimeSignaler
from ..signaler.rabbit_signaler import RabbitSignaller
from typing import Callable

class SignalerFactory(ABC):
    @staticmethod
    def create(reset_cache_callback:"Callable", signaler_options:"DictEx"=None) -> "BaseSignaler":
        if signaler_options is not None and signaler_options.has("type"):
            signaler_type = signaler_options.type
            if signaler_type == "rabbit":
                return RabbitSignaller(reset_cache_callback, signaler_options)
        return TimeSignaler(reset_cache_callback, signaler_options)