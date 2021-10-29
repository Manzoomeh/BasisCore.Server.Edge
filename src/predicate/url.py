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
    parts = url.split("/")
    l = len(parts)-1
    for index, value in enumerate(parts):
        name = "_"
        if value[0] == ':':
            name = value[1:]
            if(index == l):
                variables.append('"{0}" : "/".join({0})'.format(name))
                name = '*'+name
            else:
                variables.append('"{0}" : {0}'.format(name))
        p.append(name)
    body = """
def gfg(url):
    {0} = url.split("/")
    return {{ {1} }} """.format(
        ','.join(p),
        ','.join(variables))

    f_code = compile(body, "<str>", "exec")
    f_func = FunctionType(f_code.co_consts[0], globals(), "gfg")
    return f_func


# calliong the function
f = get_validate(":app/t/:y/:u/:l/4/t")
try:
    r = f("google.com/ali/product/type/app/343/5")
    print(r)
except Exception:
    print("ho")
