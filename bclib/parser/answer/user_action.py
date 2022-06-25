from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bclib.parser.answer.answer import Answer
from .user_action_types import UserActionTypes


class UserAction:
    """This class will be updated in next versions."""

    def __init__(self, prp_id: int, action: UserActionTypes, prp_value_id: int, value_id: int, value: any, datatype: str,
                 multi: bool, part: int, answer:'Answer'):
        self.prp_id = prp_id
        self.action = action
        self.prp_value_id = prp_value_id
        self.value_id = value_id
        self.value = value
        self.part = part
        self.datatype = datatype
        self.multi = multi
        self.answer:'Answer' = answer
    def as_tuple(self) -> tuple:
        return (self.prp_id, self.action.value, self.prp_value_id, self.value_id,
                self.value, self.part, self.datatype, self.multi,self.answer)

    def as_dict(self) -> dict:
        return {
            "prp_id": self.prp_id,
            "action": self.action.value,
            "prp_value_id": self.prp_value_id,
            "value_id": self.value_id,
            "value": self.value,
            "part": self.part,
            "datatype": self.datatype,
            "multi": self.multi,
            "answer": self.answer
        }

    def __str__(self) -> str:
        return str(self.as_tuple())

    def __repr__(self) -> str:
        return str(self.as_dict())
