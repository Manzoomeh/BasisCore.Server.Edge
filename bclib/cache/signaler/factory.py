from abc import ABC
from typing import Callable
from bclib.cache.signaler.base_signaler import BaseSignaler
from bclib.cache.signaler.no_signaler import NoSignaler
from bclib.cache.signaler.rabbit_signaler import RabbitSignaller
from bclib.utility import DictEx


class SignalerFactory(ABC):
    @staticmethod
    def create(reset_cache_callback: "Callable", signaler_options: "DictEx" = None) -> "BaseSignaler":
        """        
        This is a factory function for create signaler

        Args:
            reset_cache_callback (Callable): The function that reset cache.
            signaler_options (DictEx, optional): The options for signaler type.

        Raises:
            ValueError: If type of signaler inputs in options is not 'rabbit'

        Returns:
            BaseSignaler: BaseSignaler
        """
        if signaler_options is not None and signaler_options.has("type"):
            signaler_type = signaler_options.type
            if signaler_type == "rabbit":
                return RabbitSignaller(reset_cache_callback, signaler_options)
            else:
                raise ValueError(
                    f"Unknown type for signaler ('${signaler_type}')")
        return NoSignaler()
