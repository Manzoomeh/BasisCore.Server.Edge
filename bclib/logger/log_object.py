from typing import Dict, List

class LogObject:
    def __init__(self, schema_name: str, **kwargs) -> None:
        self.__items: Dict[str, List[List]] = dict()
        for key, value in kwargs.items():
            self.add_property(key, [value])
        self.schema_name = schema_name

    def add_property(self, prp_title: str, answer: List):
        if len(answer) > 0:
            if prp_title not in self.__items:
                self.__items[prp_title] = list()
            self.__items[prp_title].append(answer)
    
    @property
    def properties(self):
        return self.__items