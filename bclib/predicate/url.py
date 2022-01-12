from struct import error
from types import FunctionType
from bclib.context import Context
from bclib.utility import DictEx
from ..predicate.predicate import Predicate


class Url (Predicate):
    """Create Url cheking predicate"""

    def __init__(self, expression: str) -> None:
        super().__init__(expression)
        self.__validator: FunctionType = Url.__generate_validator(expression)

    def check(self, context: Context) -> bool:
        try:
            is_ok, url_parts = self.__validator(context.url)
            if is_ok and url_parts:
                context.url_segments = DictEx(url_parts)
            return is_ok
        except error as ex:
            print("Error in check url predicate", ex)
            return False

    @staticmethod
    def __generate_validator(url: str) -> FunctionType:
        segment_list = []
        return_dict_property_names = []
        where_part_list = []
        parts = url.split("/")
        last_part_index = len(parts)-1
        for index, value in enumerate(parts):
            name = "_"
            if len(value) > 0 and value[0] == ':':
                name = value[1:]
                if index == last_part_index and name[0] == '*':
                    name = name[1:]
                    return_dict_property_names.append(
                        f'"{name}" : "/".join(__{name})')
                    name = f"*__{name}"
                else:
                    return_dict_property_names.append(
                        f'"{name}" : __{name}')
                    name = f"__{name}"
            else:
                where_part_list.append(
                    f"url_parts[{index}].lower() == '{value.lower()}'")
            segment_list.append(name)
            if len(where_part_list) == 0:
                where_part_list.append("True")
        if len(return_dict_property_names) > 0:
            body = f"""
def url_function(url):
    try:
        url_parts = url.split("/")
        if {" and ".join(where_part_list)}:
            {','.join(segment_list)} = url_parts
            return (True,{{ {','.join(return_dict_property_names)} }})
        else:
            return (False,None)
    except Exception as e:
        return (False,None)"""
        else:
            body = f"""
def url_function(url):
    return (url.lower() == '{url.lower()}' ,None)"""
        f_code = compile(body, "<str>", "exec")
        f_func = FunctionType(f_code.co_consts[0], globals(), "url_function")
        return f_func
