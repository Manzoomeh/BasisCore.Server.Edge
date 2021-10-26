REQUEST_DISPATCHERDispatcher_MAIN_LOOKUP


def requestDispatcher(*decorator_args, **decorator_kwargs):
    def decorator(function):
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            return result
        dic = dict((name, decorator_kwargs[name])
                   for name in decorator_kwargs)
        SOURCE_COMMAND_ROUTER[function.__name__] = SourceCallbackInfo(
            dic, wrapper)
        return wrapper
    return decorator
