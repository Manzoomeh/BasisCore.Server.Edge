from .model import CallbackInfo
from context import Context


REQUEST_DISPATCHER_MAIN_LOOKUP = dict(str, list[CallbackInfo])


def get_lookup(key: str) -> list[CallbackInfo]:
    ret_val: None
    if key in REQUEST_DISPATCHER_MAIN_LOOKUP:
        ret_val = REQUEST_DISPATCHER_MAIN_LOOKUP[key]
    else:
        ret_val = list()
        REQUEST_DISPATCHER_MAIN_LOOKUP[key] = ret_val
    return ret_val


# def requestDispatcher(*decorator_args, **decorator_kwargs):
#     def decorator(function):
#         def wrapper(*args, **kwargs):
#             result = function(*args, **kwargs)
#             return result
#         dic = dict((name, decorator_kwargs[name])
#                    for name in decorator_kwargs)
#         SOURCE_COMMAND_ROUTER[function.__name__] = SourceCallbackInfo(
#             dic, wrapper)
#         return wrapper
#     return decorator


def contextDispatcher(context: Context):
    result = None
    name = type(context).name
    for item in get_lookup(name):
        result = item.tryExecute(context)
        if(result is not None):
            break
    return result
