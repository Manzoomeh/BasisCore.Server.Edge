from .callback_info import CallbackInfo
from context import Context


CONTEXT_DISPATCHER_LOOKUP: dict[str, list[CallbackInfo]] = dict()


def get_lookup(key: str) -> list[CallbackInfo]:
    ret_val: None
    if key in CONTEXT_DISPATCHER_LOOKUP:
        ret_val = CONTEXT_DISPATCHER_LOOKUP[key]
    else:
        ret_val = list()
        CONTEXT_DISPATCHER_LOOKUP[key] = ret_val
    return ret_val


def contextDispatcher(context: Context):
    result = None
    name = type(context).__name__
    l = get_lookup(name)
    for item in l:
        result = item.tryExecute(context)
        if(result is not None):
            break
    return result
