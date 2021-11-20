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
                return_dict_property_names.append('"{0}" : __{0}'.format(name))
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
        print(url_parts)
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
    print(body)
    print(" and ".join(where_part_list))

    f_code = compile(body, "<str>", "exec")
    f_func = FunctionType(f_code.co_consts[0], globals(), "url_function")
    return f_func


# calliong the function
# _url = ":app/Ali/:y/:u/:l/343/:t"
# _check = "google.com/ali/product/type/app/343/5/0"

# _url = "py/:g/:rkey/r/:t"
# _check = "py/ggg/1212/r/55"

_url = "PY/tt"
_check = "py/TT"

f = get_validate(_url)
ok, data = f(_check)
print(ok, data)
