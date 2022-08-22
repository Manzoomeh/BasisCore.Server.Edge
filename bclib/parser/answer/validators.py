from abc import ABC, abstractmethod
import re
from pydantic import BaseModel
def ValidationFactory(name:"str", rule:"any") -> "Validation|None":
    validations = {
        "required": RequiredValidation(name, rule),
        "minLength": MinLengthValidation(name, rule),
        "maxLength": MaxLengthValidation(name, rule), 
        "min": MinValidation(name, rule), 
        "max": MaxValidation(name, rule), 
        "dataType": DataTypeValidation(name, rule), 
        "regex": RegexValidation(name, rule),
        "national_code": NatioanalValidation(name, rule)
    }
    return validations[name] if name in validations else None

class Validation(ABC):
    def __init__(self, name:"str", rule:"any") -> None:
        self.name = name
        self.rule = rule
        self.status: "bool" = None
        self.description: "str" = None

    @abstractmethod
    def check_validation(self, value:"any"):
        pass

class RequiredValidation(Validation):
    def __init__(self, name: "str", rule:"any") -> None:
        super().__init__(name, rule)

    def check_validation(self, value: "any"):
        self.status = False if self.rule == True and not value else True
        self.description = None if self.status else "required error"

class MinLengthValidation(Validation):
    def __init__(self, name: "str", rule: "any") -> None:
        super().__init__(name, rule)

    def check_validation(self, value: "any"):
        try:
            self.status = len(value) > self.rule
            self.description = None if self.status else "min length error"
        except Exception as ex:
            self.status = False
            self.description = "min length error"

class MaxLengthValidation(Validation):
    def __init__(self, name: "str", rule: "any") -> None:
        super().__init__(name, rule)

    def check_validation(self, value: "any"):
        try:
            self.status = len(value) < self.rule
            self.description = None if self.status else "max length error"
        except Exception as ex:
            self.status = False
            self.description = "max length error"

class MinValidation(Validation):
    def __init__(self, name: "str", rule: "any") -> None:
        super().__init__(name, rule)

    def check_validation(self, value: "any"):
        try:
            self.status = value > self.rule
            self.description = None if self.status else "min value error"
        except Exception as ex:
            self.status = False
            self.description = "min value error"

class MaxValidation(Validation):
    def __init__(self, name: "str", rule: "any") -> None:
        super().__init__(name, rule)

    def check_validation(self, value: "any"):
        try:
            self.status = value < self.rule
            self.description = None if self.status else "max value error"
        except Exception as ex:
            self.status = False
            self.description = "max value error"

class DataTypeValidation(Validation):
    def __init__(self, name: "str", rule: "any") -> None:
        super().__init__(name, rule)

    def check_validation(self, value: "any"):
        types = {
            "int": self.__is_integer(value),
            "float": self.__is_float(value)
        }
        types[self.rule] if self.rule in types else self.__set_attrs()

    def __set_attrs(self):
        self.status = False
        self.description = f"check function not found for {self.rule}"

    def __is_integer(self, value: "any"):
        try:
            int(value)
            self.status == True
        except Exception:
            self.status == False
            self.description = "Value is not an integer"

    def __is_float(self, value: "any"):
        try: 
            float(value)
            self.status == True
        except Exception :
            self.status == False
            self.description = "Value is not an integer"

class RegexValidation(Validation):
    def __init__(self, name: "str", rule: "any") -> None:
        super().__init__(name, rule)

    def check_validation(self, value: "any"):
        try:
            self.status = re.search(value, self.rule) != None
            self.description = None if self.status else "regex error"
        except Exception as ex:
            self.status = False
            self.description = "regex error"

class NatioanalValidation(Validation):
    def __init__(self, name: "str", rule: "any") -> None:
        super().__init__(name, rule)
    
    def check_validation(self, value: "any"):
        pass