from abc import ABC
import re


class Validator(ABC):

    @staticmethod
    def check_validators(validators:"dict", value:"any") -> "tuple[bool, list[str]]":

        check_validation = {
            "required": Validator.required_validator(value, validators["required"]) if 'required' in validators else None,
            "minLength": Validator.min_length_validator(value, validators["minLength"]) if validators.get('minLength') is not None else None,
            "maxLength": Validator.max_length_validator(value, validators["maxLength"]) if validators.get('maxLength') is not None else None, 
            "min": Validator.min_validator(value, validators["min"]) if validators.get('min') is not None else None, 
            "max": Validator.max_validator(value, validators["max"]) if validators.get('max') is not None else None, 
            "dataType": Validator.data_type_validator(value, validators["dataType"]) if 'dataType' in validators else None,
            "regex": Validator.regex_validator(value, validators["regex"]) if 'regex' in validators else None
        }
        validations_message:"list[str]" = []
        
        for validator in validators:
            if validator in check_validation:
                checked = check_validation[validator]
                if checked is not None:
                    checked_status, checked_message = checked
                    if not checked_status:
                        validations_message.append(checked_message)

        validation_status = True if len(validations_message) == 0 else False
        return validation_status, validations_message
    
    @staticmethod
    def required_validator(value:"any", is_required:"bool") -> "tuple[bool, list[str]|None]":
        status = False if is_required and not value else True
        message = None if status else "Required validation error"
        return status, message

    @staticmethod
    def min_length_validator(value:"any", min_length:"any") -> "tuple[bool, list[str]|None]":
        try:
            min_length = min_length if isinstance(min_length, int) else int(min_length)
            status = len(value) >= min_length
        except Exception:
            status = False

        message = None if status else "Min length error"
        return status, message

    @staticmethod
    def max_length_validator(value:"any", max_length:"any") -> "tuple[bool, list[str]|None]":
        try:
            max_length = max_length if isinstance(max_length, int) else int(max_length)
            status = len(value) <= max_length
        except Exception:
            status = False

        message = None if status else "Max length error"
        return status, message
    
    @staticmethod
    def min_validator(value:"any", min_value:"int") -> "tuple[bool, list[str]|None]":
        try:
            status = int(value) >= min_value
        except Exception as ex:
            status = False
        
        message = None if status else "Min value error"
        return status, message
    
    @staticmethod
    def max_validator(value:"any", max_value:"int") -> "tuple[bool, list[str]|None]":
        try:
            status = int(value) <= max_value
        except Exception as ex:
            status = False
        
        message = None if status else "Max value error"
        return status, message 
    
    @staticmethod
    def data_type_validator(value:"any", type:"str") -> "tuple[bool, list[str]|None]":        
        message = None
        status = True
        if type in ["int", "float", "text", "ntext", "str"]:
            try:
                if type == "int":
                    int(value)
                elif type == "float":
                    float(value)
                else:
                    str(value)
            except Exception:
                status = False
            if not status:
                message = f"Type of value is not {type}"
        else:
            status = False
            message = f"Function not found for {type} type checker"

        return status, message

    @staticmethod
    def regex_validator(value:"any", regex_expression:"str") -> "tuple[bool, list[str]|None]":
        try:
            status = re.match(fr"{regex_expression}", value.strip()) != None
        except:
            status = False
        
        message = None if status else "regex error"
        return status, message