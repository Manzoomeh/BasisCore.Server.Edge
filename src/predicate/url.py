from types import FunctionType
from context import Context
from utility.DictEx import DictEx
from .predicate import Predicate


class Url (Predicate):
    """Create Url cheking predicate"""

    def __init__(self, expression) -> None:
        super().__init__(expression)
        self.__validator = Url.__generate_validator(expression)

    def check(self, context: Context) -> bool:
        try:
            is_ok, url_parts = self.__validator(context.request.request.url)
            if is_ok and url_parts:
                print(url_parts)
                context.url_segments = DictEx(url_parts)
            return is_ok
        except:
            return False

    @staticmethod
    def __generate_validator(url) -> FunctionType:
        p = []
        variables = []
        where_part = []
        parts = url.lower().split("/")
        l = len(parts)-1
        for index, value in enumerate(parts):
            name = "_"
            if len(value) > 0 and value[0] == ':':
                name = value[1:]
                if(index == l):
                    variables.append(
                        '"{0}" : "/".join(__{0})'.format(name))
                    name = '*'+"__{0}".format(name)
                else:
                    variables.append('"{0}" : __{0}'.format(name))
                    name = "__{0}".format(name)
            else:
                where_part.append(
                    "url_parts[{0}] == '{1}'".format(index, value))
            p.append(name)
        body = """
def gfg(url):
    url_parts = url.lower().split("/")
    print(url_parts)
    if {0}:
        {1} = url_parts
        return (True,{{ {2} }})
    else:
        return (False,None)""".format(
            " and ".join(where_part),
            ','.join(p),
            ','.join(variables))
        f_code = compile(body, "<str>", "exec")
        f_func = FunctionType(f_code.co_consts[0], globals(), "gfg")
        return f_func
