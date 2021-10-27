from context import SourceContext
from context import SourceMemberContext
from predicate import Predicate
from ..callback_info import CallbackInfo
from ..dispatcher import dispatch_context, get_context_lookup


def source_action(*predicates: (Predicate)):
    def _decorator(function):
        def _wrapper(context: SourceContext):
            function(context)
            if(context.data is not None):
                for member in context.command.member:
                    member_context = SourceMemberContext(context, member)
                    dispatch_context(member_context)
                print(context)
            return True
        get_context_lookup(SourceContext.__name__)\
            .append(CallbackInfo([*predicates], _wrapper))
        return _wrapper
    return _decorator
