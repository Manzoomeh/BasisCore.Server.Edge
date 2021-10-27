from context import SourceContext
from context import SourceMemberContext
from predicate import Predicate
from ..callback_info import CallbackInfo
from ..dispatcher import dispatch_context, get_context_lookup


def source_action(*predicates: (Predicate)):
    def _decorator(function):
        def _wrapper(context: SourceContext):
            function(context)
            result_set = list()

            if(context.data is not None):
                for member in context.command.member:
                    member_context = SourceMemberContext(context, member)
                    dispatch_context(member_context)
                    result = {
                        "options": {
                            "tableName": member_context.table_name,
                            "keyFieldName": member_context.key_field_name,
                            "statusFieldName": member_context.status_field_name,
                            "mergeType": member_context.merge_type.value[0]
                        },
                        "data": member_context.result
                    }
                    result_set.append(result)
            return result_set
        get_context_lookup(SourceContext.__name__)\
            .append(CallbackInfo([*predicates], _wrapper))
        return _wrapper
    return _decorator
