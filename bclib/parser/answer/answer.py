import json
from typing import Any, Callable

from bclib.parser.answer.enriched_data import EnrichedData
from bclib.parser.answer.storage_data import StorageData
from bclib.parser.answer.question_data import QuestionData
from bclib import parser
from bclib.db_manager import RESTfulConnection
from bclib.parser.answer.validators import Validator
from bclib.utility import DictEx
from ..answer.user_action_types import UserActionTypes
from ..answer.user_action import UserAction
import asyncio

class Answer:
    """BasisJsonParser is a tool to parse basis_core components json objects. This tool is developed based on
             basis_core key and values."""

    def __init__(self, data: 'str|Any', api_url: 'str' = None, check_validation:"bool"= False):
        self.json = json.loads(data) if isinstance(data, str) else data
        self.__answer_list: 'list[UserAction]' = None
        self.__api_connection = RESTfulConnection(
            api_url) if api_url else None
        self.check_validation = check_validation 

    async def __fill_answer_list_async(self):
        self.__answer_list = list()
        internal_prp_value_index = 1
        for data in self.json['properties']:
            multi = data['multi'] if 'multi' in data else None
            for action_type in UserActionTypes:
                if action_type.value in list(data.keys()):
                    prp_id = data['propId'] if action_type != UserActionTypes.ANSWERS else data["prpId"]
                    for actions in data[action_type.value]:
                        prp_value_id = actions['id'] if 'id' in actions.keys() else None
                        if 'parts' in actions.keys():
                            for parts in actions['parts']:
                                internal_prp_value_id = internal_prp_value_index
                                part_number = parts['part'] if "part" in parts.keys() else None
                                for values in parts['values']:
                                    value_id = values['id'] if "id" in values.keys() else None
                                    value = values['value']
                                    answer = parser.ParseAnswer(
                                        values["answer"]) if 'answer' in values.keys() else None
                                    self.__answer_list.append(
                                        UserAction(
                                            prp_id, action_type, prp_value_id, internal_prp_value_id, value_id, value, None, multi, part_number, answer
                                        )
                                    )
                        else:
                            internal_prp_value_id = internal_prp_value_index
                            self.__answer_list.append(
                                UserAction(
                                    prp_id, action_type,  prp_value_id, internal_prp_value_id, None, None, None, multi, None, None
                                )
                            )
                        internal_prp_value_index += 1

        await self.__enrich_data_async()

    async def __enrich_data_async(self):
        questions_info: "list[QuestionData]" = list()
        if self.__api_connection:
            questions_data = DictEx(await self.__api_connection.get_async())
            for data in questions_data.sources:
                for question in data.data:
                    for parts in question.questions:
                        enriched_data_list: "list[EnrichedData]" = [
                            self.__enrich_data(validations)
                            for validations in parts.parts
                        ]
                        questions_info.append(
                            QuestionData(parts.prpId, parts.OwnerID, parts.TypeID if "TypeID" in parts else parts.typeid, parts.wordId, enriched_data_list)
                        )
        if len(questions_info) > 0:
            for values in self.__answer_list:
                for data in questions_info:
                    if int(data.prpid) == int(values.prp_id):
                        values.ownerid = data.ownerid
                        values.typeid = data.typeid
                        values.wordid = data.wordid
                        for enriched_data in data.enriched_data:
                            if (enriched_data.part == values.part) or (values.part is None):
                                values.datatype = enriched_data.data_type
                                storage_data = enriched_data.storage_data
                                if storage_data:
                                    values.database = storage_data.data_base
                                    values.table = storage_data.table
                                    values.field = storage_data.field
                                if self.check_validation and values.action != UserActionTypes.DELETED:
                                    status, message = Validator.check_validators(enriched_data.validators, values.value)
                                    values.validation_status = status
                                    values.validation_message = message
                
    def __enrich_data(self, validations:DictEx) -> 'EnrichedData':
        part_id = validations.part
        data_type = self.__set_data_type(validations)
        val_val = validations.validations
        storage_data = self.__set_storage_data(val_val) if isinstance(val_val, dict) else None
        validators = val_val if self.check_validation and isinstance(validations.validations, dict) else {}
        return EnrichedData(part_id, data_type, storage_data, validators)

    def __set_data_type(self, validations:DictEx) -> 'str':
        has_link = True if validations.link else False
        val_val = validations.validations
        data_type = val_val["dataType"] if isinstance(val_val, dict) and "dataType" in val_val else None
        
        return self.__data_type_checker(validations.viewType, data_type, has_link)

    def __data_type_checker(self, view_type: str, datatype: str = None, has_link: bool = None):
        if view_type in ["select", "checklist", "radio"]:
            if has_link == True:
                result = "urlvalue"
            else:
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
        elif view_type in ["upload", "blob"]:
            result = "files"
        elif view_type == "color":
            result = "textvalue"
        elif view_type == "reference":
            result = "reference"
        else:
            result = "None"
        return result
    
    def __set_storage_data(self, val_val:"dict") -> "StorageData":
        database = val_val["database"] if "database" in val_val else None
        table = val_val["table"] if "table" in val_val else None
        field = val_val["field"] if "field" in val_val else None
        return StorageData(database, table, field)
                
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

    async def is_valid_answer_async(self):
        if self.__answer_list is None:
            await self.__fill_answer_list_async()
        is_valid = True
        for user_action in self.__answer_list:
            if user_action.validation_status == False:
                print(user_action.validation_message)
                is_valid = False
                break
        return is_valid
