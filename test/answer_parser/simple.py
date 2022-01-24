from bclib import parser

js = {
    "schemaId": 1161,
    "lid": 1,
    "usedForId": 1423330,
    "properties": [
        {
            "propId": 12345,
            "edited": [
                {
                    "id": 123152,
                    "parts": [
                        {
                            "part": 1,
                            "values": [
                                {
                                    "id": 1,
                                    "value": "دیزل جدید"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "propId": 1000,
            "edited": [
                {
                    "id": 45615,
                    "parts": [
                        {
                            "part": 1,
                            "values": [
                                {
                                    "id": 59757,
                                    "value": "3"
                                }
                            ]
                        },
                        {
                            "part": 2,
                            "values": [
                                {
                                    "id": 85257,
                                    "value": "1500"
                                }
                            ]
                        },
                        {
                            "part": 3,
                            "values": [
                                {
                                    "id": 78957,
                                    "value": "500"
                                }
                            ]
                        }
                    ]
                },
                {
                    "id": 156852,
                    "parts": [
                        {
                            "part": 2,
                            "values": [
                                {
                                    "id": 79457,
                                    "value": "2000"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "propId": 1004,
            "added": [
                {

                    "parts": [
                        {
                            "part": 1,
                            "values": [
                                {
                                    "value": "this is a test to check"
                                }
                            ]
                        }
                    ]
                },
                {
                    "parts": [
                        {
                            "part": 1,
                            "values": [
                                {
                                    "value": "0"
                                }
                            ]
                        }
                    ]
                }
            ],
            "deleted": [
                {
                    "id": 8
                }
            ]
        },
        {
            "propId": 1007,
            "added": [
                {
                    "id": 2,
                    "parts": [
                        {
                            "part": 1,
                            "values": [
                                {
                                    "value": "this is a test to ckeck is add working or not"
                                }
                            ]
                        }
                    ]
                }
            ],
            "deleted": [
                {
                    "id": 3086725,
                    "parts": [
                        {
                            "part": 1,
                            "values": [
                                {
                                    "id": 10,
                                    "value": "2222"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "propId": 130621,
            "edited": [
                {
                    "id": 8456215,
                    "parts": [
                        {
                            "part": 1,
                            "values": [
                                {
                                    "id": 78854,
                                    "value": "SAAAAALAAAAAM"
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "propId": 130631,
            "edited": [
                {
                    "id": 8456215,
                    "parts": [
                        {
                            "part": 2,
                            "values": [
                                {
                                    "id": 85257,
                                    "value": "1500"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}
for action_type in parser.UserActionTypes:
    print(action_type.value)

print(parser.UserActionTypes("edited"))
my_object = parser.ParseAnswer(js)
# print(my_object.actions())
print(my_object.get_actions(prp_id=12345))
print('f', my_object.get_actions(predicate=lambda x: x.prp_id ==
      12345 or x.action == parser.UserActionTypes.DELETED))
# print(my_object.actions(prpid=[1000,12345],))
# print(my_object.actions(action='deleted'))
# print(my_object.actions(action=['deleted', 'added']))
print(my_object.get_actions(action=[
      parser.UserActionTypes.EDITED, parser.UserActionTypes.ADDED], part=[1, 2]))
# print(my_object.actions(prpid=12344, action='edit', part=2))
