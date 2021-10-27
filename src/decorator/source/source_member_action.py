from context import SourceMemberContext
from predicate import Predicate
from ..callback_info import CallbackInfo
from ..dispatcher import get_context_lookup


def source_member_action(*predicates: (Predicate)):
    def _decorator(function):
        def _wrapper(context: SourceMemberContext):
            function(context)
            print(context)
            return True
        get_context_lookup(SourceMemberContext.__name__)\
            .append(CallbackInfo([*predicates], _wrapper))
        return _wrapper
    return _decorator
