from .callback_info import CallbackInfo
from predicate import Predicate
from context import SourceContext, SourceMemberContext, Context


class Dispatcher:
    def __init__(self):
        self.__look_up: dict[str, list[CallbackInfo]] = dict()

    def source_action(self, *predicates: (Predicate)):
        def _decorator(function):
            def _wrapper(context: SourceContext):
                function(context)
                result_set = list()
                if(context.data is not None):
                    for member in context.command.member:
                        member_context = SourceMemberContext(context, member)
                        self.dispatch_context(member_context)
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
            self.get_context_lookup(SourceContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def source_member_action(self, *predicates: (Predicate)):
        def _decorator(function):
            def _wrapper(context: SourceMemberContext):
                function(context)
                return True
            self.get_context_lookup(SourceMemberContext.__name__)\
                .append(CallbackInfo([*predicates], _wrapper))
            return _wrapper
        return _decorator

    def get_context_lookup(self, key: str) -> list[CallbackInfo]:
        ret_val: None
        if key in self.__look_up:
            ret_val = self.__look_up[key]
        else:
            ret_val = list()
            self.__look_up[key] = ret_val
        return ret_val

    def dispatch_context(self, context: Context):
        result = None
        name = type(context).__name__
        items = self.get_context_lookup(name)
        for item in items:
            result = item.try_execute(context)
            if(result is not None):
                break
        return result
