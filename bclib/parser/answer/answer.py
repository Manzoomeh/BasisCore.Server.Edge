import json
from typing import Any, Callable
from bclib import parser
from bclib.db_manager import RESTfulConnection
from bclib.utility import DictEx
from ..answer.user_action_types import UserActionTypes
from ..answer.user_action import UserAction


class Answer:
    """BasisJsonParser is a tool to parse basis_core components json objects. This tool is developed based on
             basis_core key and values."""

    def __init__(self, data: 'str|Any', api_url: 'str' = None):
        self.json = json.loads(data) if isinstance(data, str) else data
        self.__answer_list: 'list[UserAction]' = None
        self.__api_connection = RESTfulConnection(
            api_url) if api_url else None

    async def __fill_answer_list_async(self):
        self.__answer_list = list()
        internal_prp_value_index = 1
        for data in self.json['properties']:
            multi = data['multi'] if 'multi' in data else None
            for action_type in UserActionTypes:
                if action_type.value in list(data.keys()):
                    for actions in data[action_type.value]:
                        if 'parts' in actions.keys():
                            for parts in actions['parts']:
                                internal_prp_value_id = internal_prp_value_index
                                for values in parts['values']:
                                    prp_id = data['propId']
                                    prp_value_id = actions['id'] if 'id' in actions.keys(
                                    ) else None
                                    part_number = parts['part'] if "part" in parts.keys(
                                    ) else None
                                    value_id = values['id'] if "id" in values.keys(
                                    ) else None
                                    value = values['value']
                                    answer = parser.ParseAnswer(
                                        values["answer"]) if 'answer' in values.keys() else None
                                    self.__answer_list.append(UserAction(
                                        prp_id, action_type, prp_value_id, internal_prp_value_id, value_id, value, None, multi, part_number, answer))
                        else:
                            internal_prp_value_id = internal_prp_value_index
                            prp_id = data['propId']
                            prp_value_id = actions['id'] if 'id' in actions.keys(
                            ) else None
                            self.__answer_list.append(UserAction(
                                prp_id, action_type,  prp_value_id, internal_prp_value_id, None, None, None, multi, None, None))
                        internal_prp_value_index += 1
        await self.__try_set_data_type_async()

    async def __get_action_async(self, prp_id_list: 'list[int]', action_list: 'list[UserActionTypes]', part_list: 'list[int]', is_file: "bool" = None, predicate: 'Callable[[UserAction],bool]' = None) -> 'list[UserAction]':
        ret_val: 'list[UserAction]' = None
        if self.__answer_list is None:
            await self.__fill_answer_list_async()
        if predicate:
            if is_file == None:
                ret_val = [x for x in self.__answer_list if predicate(x)]
            else:
                ret_val = [x for x in self.__answer_list if predicate(
                    x) and x.is_file_content() == is_file]
        else:
            ret_val = [x for x in self.__answer_list if
                       (prp_id_list is None or x.prp_id in prp_id_list) and
                       (action_list is None or x.action in action_list) and
                       (part_list is None or x.part in part_list) and
                       (is_file is None or x.is_file_content() == is_file)
                       ]

        return ret_val if ret_val else list()

    async def get_actions_async(self, prp_id: 'int|list[int]' = None, action: 'UserActionTypes|list[UserActionTypes]' = None,
                                part: int = None, is_file: "bool" = None, predicate: 'Callable[[UserAction],bool]' = None) -> 'list[UserAction]':
        """
        inputs:
        prpid: None, int or list[int]
        action: None, int or list[int]
        part: None or int
        Samples:
        (prpid=None, action='edited')
        (prpid=[12345, 1000], action=None)
        """

        action_list = [action] if isinstance(
            action, UserActionTypes) else action
        prp_id_list = [prp_id] if isinstance(prp_id, int) else prp_id
        part_list = [part] if isinstance(part, int) else part
        return await self.__get_action_async(prp_id_list, action_list, part_list, is_file, predicate)

    def __data_type_checker(self, view_type: str, datatype: str = None, has_link: bool = None):

        if view_type in ["select", "checklist", "radio"]:
            if has_link == True:
                result = "urlvalue"
            result = "fixvalue"
        elif view_type == "textarea":
            result = "ntextvalue"
        elif view_type == "text" and datatype in ["text", "None", None]:
            result = "textvalue"
        elif view_type == "text" and datatype == "int":
            result = "numvalue"
        elif view_type == "text" and datatype == "float":
            result = "floatvalue"
        elif view_type == "autocomplete":
            result = "urlvalue"
        elif view_type == "upload":
            result == "files"
        else:
            result = "None"
        return result

    async def __try_set_data_type_async(self):
        if self.__api_connection:
            type_list = list()
            questions_data = DictEx(await self.__api_connection.post_async())
            for data in questions_data.sources:
                for question in data.data:
                    for parts in question.questions:
                        for validations in parts.parts:
                            has_link = True if validations.link else False
                            data_type = validations.validations["datatype"] if isinstance(validations.validations, dict) and "datatype" in validations.validations.keys(
                            ) else "None"
                            type_list.append({
                                "prpId": parts.prpId, "part": validations.part, "viewtype": validations.viewType,
                                "datatype": data_type, "table": self.__data_type_checker(validations.viewType, data_type, has_link)
                            })
            for type in type_list:
                for values in self.__answer_list:
                    if int(type['prpId']) == int(values.prp_id) and type["part"] == values.part or values.part is None:
                        values.datatype = type['table']

    async def get_added_actions_async(self, prp_id: 'int|list[int]' = None, predicate: 'Callable[[UserAction],bool]' = None) -> 'list[list[list[UserAction]]]':
        return await self.__get_specify_actions(UserActionTypes.ADDED, prp_id, predicate)

    async def get_edited_actions_async(self, prp_id: 'int|list[int]' = None, predicate: 'Callable[[UserAction],bool]' = None) -> 'list[list[list[UserAction]]]':
        return await self.__get_specify_actions(UserActionTypes.EDITED, prp_id, predicate)

    async def __get_specify_actions(self, action_type: UserActionTypes, prp_id: 'int|list[int]' = None, predicate: 'Callable[[UserAction],bool]' = None) -> 'list[list[list[UserAction]]]':
        ret_val: "dict[int,list[list[UserAction]]]" = {}
        action_objects = await self.get_actions_async(prp_id=prp_id, action=action_type, predicate=predicate)
        unique_internal_values_id = set(
            [obj.internal_prp_value_id for obj in action_objects])
        same_internal_value_id_objects = [[obj for obj in action_objects if obj.internal_prp_value_id ==
                                           internal_values_id] for internal_values_id in unique_internal_values_id]
        unique_prp_id = set(
            [obj[0].prp_id for obj in same_internal_value_id_objects])
        for _prp_id in unique_prp_id:
            for obj in same_internal_value_id_objects:
                if obj[0].prp_id == _prp_id:
                    if obj[0].prp_id in ret_val:
                        ret_val[obj[0].prp_id].append(obj)
                    else:
                        ret_val[obj[0].prp_id] = [obj]
        return list(ret_val.values())
