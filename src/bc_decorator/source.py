from typing import Callable
from bc_decorator.model import CallbackInfo
from context import DbSourceRequestContext
from .model import CallbackResult, PredicateDic


SOURCE_COMMAND_ROUTER = dict()


class SourceCallbackInfo(CallbackInfo):
    def __init__(self, predicates: PredicateDic, callback: Callable[[DbSourceRequestContext], CallbackResult]) -> CallbackResult:
        super().__init__(predicates, callback)

    def getValue(self, propertyName, context: DbSourceRequestContext):
        return context.command.attributes[propertyName]


def sourceAction(*args1, **kwargs1):
    def decorator(function):
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            return result
        dic = dict((name, kwargs1[name])
                   for name in kwargs1)
        SOURCE_COMMAND_ROUTER[function.__name__] = SourceCallbackInfo(
            dic, wrapper)
        return wrapper
    return decorator


def sourceCommandDispatcher(request: DbSourceRequestContext):
    result = None
    for handlerName in SOURCE_COMMAND_ROUTER:
        result = SOURCE_COMMAND_ROUTER[handlerName].tryExecute(
            request)
        if(result != None):
            break
    return result
