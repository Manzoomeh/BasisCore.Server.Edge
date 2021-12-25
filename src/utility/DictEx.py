class DictEx(dict):
    """Extended version of dict class for dot.notation access to attributes"""

    def __init__(self, *args, **kwargs):
        for arg in args:
            if isinstance(arg, dict):
                DictEx.fill_from_dic(self, arg)

    @classmethod
    def create(cls, data: dict):
        ret_val = DictEx()
        for k, v in data.items():
            if isinstance(v, dict):
                ret_val[k] = DictEx.create(v)
            elif isinstance(v, list):
                ret_val[k] = DictEx.file_from_list(v)
            else:
                ret_val[k] = v
        return ret_val

    @classmethod
    def fill_from_dic(cls, new, data: dict):
        for k, v in data.items():
            if isinstance(v, dict):
                new[k] = DictEx.create(v)
            elif isinstance(v, list):
                new[k] = DictEx.file_from_list(v)
            else:
                new[k] = v

    @classmethod
    def file_from_list(cls, data: list):
        ret_val_list = list()
        for item in data:
            if isinstance(item, dict):
                ret_val_list.append(DictEx.create(item))
            elif isinstance(item, list):
                ret_val_list.append(DictEx.file_from_list(item))
            else:
                ret_val_list.append(item)
        return ret_val_list

    __getattr__ = dict.get
