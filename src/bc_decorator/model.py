from typing import Callable, TypedDict
from context import RequestContext
from predicate import PredicateBase


class PredicateDic(TypedDict):
    property: str
    predicate: PredicateBase


class CallbackResult:
    def __init__(self, result) -> None:
        self.result = result
        self.processed = True if (result == None) else False
        pass


class CallbackInfo:
    def __init__(self, predicates: PredicateDic,  callback: Callable[[RequestContext], CallbackResult]) -> CallbackResult:
        self.__callback = callback
        self.__predicates = predicates

    def tryExecute(self, context: RequestContext) -> CallbackResult:
        isMatch = True
        for propertyName in self.__predicates:
            value = self.getValue(propertyName, context)
            isMatch = self.__predicates[propertyName].isMatch(value, context)
            if(isMatch == False):
                break
        return self.__callback(context) if(isMatch == True) else None

    def getValue(self, propertyName, context: RequestContext):
        return None
