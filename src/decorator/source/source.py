from context import SourceContext
from ..callback_info import CallbackInfo
from ..dispatcher import get_context_lookup


def source_action(*predicates):
    def _decorator(function):
        def _wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            return result
        get_context_lookup(SourceContext.__name__)\
            .append(CallbackInfo([*predicates], _wrapper))
        return _wrapper
    return _decorator
