import json
from typing import Any
from .user_action_types import UserActionTypes
from .user_action import UserAction


class Answer:
    """BasisJsonParser is a tool to parse basis_core components json objects. This tool is developed based on
             basis_core key and values."""

    def __init__(self, data: 'str|Any'):
        self.json = json.loads(data) if isinstance(data, str) else data
        self.__answer_list: 'list[UserAction]' = None

    # Create a flat data.
    def __fill_answer_list(self):

        self.__answer_list = list()
        for data in self.json['properties']:
            for action_type in UserActionTypes:
                if action_type.value in list(data.keys()):
                    for actions in data[action_type.value]:
                        if 'parts' in actions.keys():
                            for parts in actions['parts']:
                                for values in parts['values']:
                                    prp_id = data['propId']
                                    prp_value_id = actions['id'] if 'id' in actions.keys(
                                    ) else None
                                    part_number = parts['part'] if "part" in parts.keys(
                                    ) else None
                                    value_id = values['id'] if "id" in values.keys(
                                    ) else None
                                    value = values['value']
                                    self.__answer_list.append(UserAction(
                                        prp_id, action_type, prp_value_id, value_id, value, None, None, part_number))
                        else:
                            prp_id = data['propId']
                            prp_value_id = actions['id'] if 'id' in actions.keys(
                            ) else None
                            self.__answer_list.append(UserAction(
                                prp_id, action_type,  prp_value_id, None, None, None, None, None))

        return self.__answer_list

    def __get_action(self, prp_id_list: 'list[int]', action_list: 'list[UserActionTypes]', part_list: 'list[int]') -> 'list[UserAction]':

        content = list()
        if self.__answer_list is None:
            self.__fill_answer_list()

        return [x for x in self.__answer_list if
                (prp_id_list is None or x.prp_id in prp_id_list) and
                (action_list is None or x.action in action_list) and
                (part_list is None or x.part in part_list)
                ]

        return content

    def get_actions(self, prp_id: 'int|list[int]' = None, action: 'UserActionTypes|list[UserActionTypes]' = None,
                    part: int = None) -> 'list[UserAction]':
        """
        inputs:
        prpid: None, int or list
        action: None, int or list
        part: None or in
        Samples:
        (prpid=None, action='edited')
        (prpid=[12345, 1000], action=None)
        """

        action_list = [action] if isinstance(
            action, UserActionTypes) else action
        prp_id_list = [prp_id] if isinstance(prp_id, int) else prp_id
        part_list = [part] if isinstance(part, int) else part

        return self.__get_action(prp_id_list, action_list, part_list)
