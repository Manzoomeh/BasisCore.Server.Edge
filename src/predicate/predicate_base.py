from context import RequestContext


class PredicateBase:
    def isMatch(self, value: any, context: RequestContext) -> bool:
        pass
