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
            ret_val[k] = DictEx.create(v) if isinstance(v, dict) else v
        return ret_val

    @classmethod
    def fill(cls, new, data: dict):
        for k, v in data.items():
            new[k] = DictEx.create(v) if isinstance(v, dict) else v

    __getattr__ = dict.get
