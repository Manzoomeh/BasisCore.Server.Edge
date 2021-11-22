from types import FunctionType
from typing import Any
from context import Context
from utility import DictEx
from .predicate import Predicate


class Url (Predicate):
    """Create Url cheking predicate"""

    def __init__(self, expression: str) -> None:
        super().__init__(expression)
        self.__validator = Url.__generate_validator(expression)

    def check(self, context: Context) -> bool:
        try:
            is_ok, url_parts = self.__validator(context.request.request.url)
            if is_ok and url_parts:
                context.url_segments = DictEx(url_parts)
            return is_ok
        except:
            return False

    @staticmethod
    def __generate_validator(url: str) -> FunctionType:
        segment_list = []
        return_dict_property_names = []
        where_part_list = []
        url = url.lower()
        parts = url.split("/")
        last_part_index = len(parts)-1
        for index, value in enumerate(parts):
            name = "_"
            if len(value) > 0 and value[0] == ':':
                name = value[1:]
                if(index == last_part_index):
                    return_dict_property_names.append(
                        '"{0}" : "/".join(__{0})'.format(name))
                    name = '*'+"__{0}".format(name)
                else:
                    return_dict_property_names.append(
                        '"{0}" : __{0}'.format(name))
                    name = "__{0}".format(name)
            else:
                where_part_list.append(
                    "url_parts[{0}] == '{1}'".format(index, value))
            segment_list.append(name)
        if len(return_dict_property_names) > 0:
            body = """
def url_function(url):
    try:
        url_parts = url.lower().split("/")
        if {0}:
            {1} = url_parts
            return (True,{{ {2} }})
        else:
            return (False,None)
    except:
        return (False,None)""".format(
                " and ".join(where_part_list),
                ','.join(segment_list),
                ','.join(return_dict_property_names))
        else:
            body = """
def url_function(url):
    return (url.lower() == '{0}' ,None)""".format(url)
        f_code = compile(body, "<str>", "exec")
        f_func = FunctionType(f_code.co_consts[0], globals(), "url_function")
        return f_func
