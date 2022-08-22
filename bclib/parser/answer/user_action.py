from typing import TYPE_CHECKING

from bclib.parser.answer.validators import Validation
if TYPE_CHECKING:
    from bclib.parser.answer.answer import Answer
from ..answer.user_action_types import UserActionTypes
from ..answer.file_user_action import FileUserAction


class UserAction:
    """This class will be updated in next versions."""

    def __init__(self, prp_id: 'int', action: 'UserActionTypes', prp_value_id: 'int', internal_prp_value_id: 'int', value_id: 'int', value: 'any', datatype: 'str',
                 multi: 'bool', part: 'int', answer: 'Answer'):
        self.prp_id = prp_id
        self.action = action
        self.prp_value_id = prp_value_id
        self.value_id = value_id
        self.value = value
        self.part = part
        self.datatype = datatype
        self.multi = multi
        self.answer: 'Answer' = answer
        self.internal_prp_value_id: "int" = internal_prp_value_id
        self.database:"str" = None
        self.table:"str" = None
        self.field:"str" = None
        self.validation_status: "bool" = True
        self.description: "list[str]" = []

    def as_tuple(self) -> tuple:
        return (self.prp_id, self.action.value, self.prp_value_id, self.internal_prp_value_id, self.value_id,
                self.value, self.part, self.datatype, self.multi, self.answer, self.validation_status, self.description)

    def as_dict(self) -> dict:
        return {
            "prp_id": self.prp_id,
            "action": self.action.value,
            "prp_value_id": self.prp_value_id,
            "internal_prp_value_index": self.internal_prp_value_id,
            "value_id": self.value_id,
            "value": self.value,
            "part": self.part,
            "datatype": self.datatype,
            "multi": self.multi,
            "answer": self.answer,
            "validation_status": self.validation_status,
            "description": self.description
        }

    def is_file_content(self):
        is_file = False
        if isinstance(self.value, dict):
            is_file = {"name", "size", "type"}.issubset(set(self.value.keys()))
        return is_file

    def as_file_content(self) -> 'FileUserAction':
        if self.is_file_content():
            value = self.value
            return FileUserAction(self.prp_id, self.prp_value_id, self.value_id, value["name"], value["type"], value["size"], value["content"])

    def __str__(self) -> str:
        return str(self.as_tuple())

    def __repr__(self) -> str:
        return str(self.as_dict())
