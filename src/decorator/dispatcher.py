from context import Context
from .callback_info import CallbackInfo


CONTEXT_DISPATCHER_LOOKUP: dict[str, list[CallbackInfo]] = dict()


def get_context_lookup(key: str) -> list[CallbackInfo]:
    ret_val: None
    if key in CONTEXT_DISPATCHER_LOOKUP:
        ret_val = CONTEXT_DISPATCHER_LOOKUP[key]
    else:
        ret_val = list()
        CONTEXT_DISPATCHER_LOOKUP[key] = ret_val
    return ret_val


def dispatch_context(context: Context):
    result = None
    name = type(context).__name__
    items = get_context_lookup(name)
    for item in items:
        result = item.try_execute(context)
        if(result is not None):
            break
    return result
