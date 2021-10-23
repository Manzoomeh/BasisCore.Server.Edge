from bc_decorator.model import CallbackInfo


SOURCE_COMMAND_ROUTER = dict()


def sourceAction(*args1, **kwargs1):
    def decorator(function):
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            return result
        dic = dict((name, kwargs1[name])
                   for name in kwargs1)
        SOURCE_COMMAND_ROUTER[function.__name__] = CallbackInfo(
            dic, wrapper)
        return wrapper
    return decorator
