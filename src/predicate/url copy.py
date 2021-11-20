from types import FunctionType
# from context import Context
# from .predicate import Predicate


# class Url(Predicate):
#     """Create url cheking predicate and also extract custom fragment from url"""

#     def __init__(self, expression, *items) -> None:
#         super().__init__(expression)
#         self.__items = [*items]

#     def check(self, context: Context) -> bool:
#         value = eval(self.exprossion, {}, {"context": context})
#         return value in self.__items


def get_validate(url):
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
            where_part.append("url_parts[{0}] == '{1}'".format(index, value))
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

    print(body)
    print(" and ".join(where_part))

    f_code = compile(body, "<str>", "exec")
    f_func = FunctionType(f_code.co_consts[0], globals(), "gfg")
    return f_func


# calliong the function
# _url = ":app/Ali/:y/:u/:l/343/:t"
# _check = "google.com/ali/product/type/app/343/5/0"
_url = "py/:rkey/r/:t"
_check = "py/1212"


f = get_validate(_url)
try:
    ok, data = f(_check)

    print(ok, data)
except Exception:
    print("ho")
