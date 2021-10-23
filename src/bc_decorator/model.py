from typing import Callable, TypedDict
from context import RequestContext
from predicate.IPredicate import IPredicate


class PredicateDic(TypedDict):
    property: str
    predicate: IPredicate


class CallbackResult:
    def __init__(self, result) -> None:
        self.result = result
        self.processed = True if (result == None) else False
        pass


class CallbackInfo:
    def __init__(self, predicates: PredicateDic,  callback: Callable[[RequestContext], CallbackResult]) -> None:
        self.__callback = callback
        self.__predicates = predicates

    # def tryExecute(self, context: RequestContext) -> CallbackResult:
    #     isMatch = True
    #     for p in self.__predicates:
    #         value = element.attributes[p]
    #         isMatch = self.__predicates[p].isMatch(value)
    #         if(isMatch == False):
    #             break
    #     return self.__callback(element, request) if(isMatch == True) else None
