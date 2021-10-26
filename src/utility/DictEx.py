class DictEx(dict):
    """Extended version of dict class for dot.notation access to attributes"""

    def __init__(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, dict):
                DictEx.fill(self, arg)

    @classmethod
    def create(cls, data: dict):
        ret_val = DictEx()
        for k, v in data.items():
            if isinstance(v, dict):
                ret_val[k] = DictEx.create(v)
            elif isinstance(v, list):
                lst = list()
                for item in v:
                    lst.append(DictEx.create(item))
                ret_val[k] = lst
            else:
                ret_val[k] = v
        return ret_val

    @classmethod
    def fill(cls, new, data: dict):
        for k, v in data.items():
            if isinstance(v, dict):
                new[k] = DictEx.create(v)
            elif isinstance(v, list):
                lst = list()
                for item in v:
                    lst.append(DictEx.create(item))
                new[k] = lst
            else:
                new[k] = v

    __getattr__ = dict.get
