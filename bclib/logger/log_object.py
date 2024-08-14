from typing import Dict, List

class LogObject:
    def __init__(self, **kwargs) -> None:
        if "schema_name" not in kwargs:
            raise Exception("'schema_name' not set for apply logging!")
        self.__items: Dict[str, List[List]] = dict()
        self.__schema_name = kwargs.pop("schema_name")
        for key, value in kwargs.items():
            self.add_property(key, [value])

    def add_property(self, prp_title: str, answer: List):
        if len(answer) > 0:
            if prp_title not in self.__items:
                self.__items[prp_title] = list()
            self.__items[prp_title].append(answer)
    
    @property
    def schema_name(self):
        return self.__schema_name

    @property
    def properties(self):
        return self.__items