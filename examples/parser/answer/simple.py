import asyncio
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
                        },
                        {
                            "part": 2,
                            "values": [
                                {
                                    "value": "this is a test"
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
                        },
                        {
                            "part": 2,
                            "values": [
                                {
                                    "value": "this"
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
                                    "value": "test",
                                    "answer": {
                                        "lid": 1,
                                        "paramUrl": "/1164",
                                        "schemaId": 1164,
                                        "schemaVersion": 1.1,
                                        "usedForId": 1423332,
                                        "properties": [
                                        {
                                            "propId": 13060,
                                            "multi": True,
                                            "edited": [
                                            {
                                            "id": 8456251,
                                            "parts": [
                                            {
                                                "part": 1,
                                                "values": [
                                                {
                                                "id": 123,
                                                "value": "5"
                                                }
                                                ]
                                            }
                                            ]
                                            }
                                            ]
                                        }
                                        ]
                                        }
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
                                    "value": "1500", 
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

async def f():
    my_object = parser.ParseAnswer(js)
    print(await my_object.get_actions_async())
if __name__ == "__main__":
    asyncio.run(f())

# display flat of js completely 
# it returns a list