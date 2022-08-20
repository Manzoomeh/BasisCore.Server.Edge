import asyncio
from bclib import parser

# js = {
#     "schemaId": 1161,
#     "lid": 1,
#     "usedForId": 1423330,
#     "properties": [
#         {
#             "propId": 12345,
#             "edited": [
#                 {
#                     "id": 123152,
#                     "parts": [
#                         {
#                             "part": 1,
#                             "values": [
#                                 {
#                                     "id": 1,
#                                     "value": "دیزل جدید"
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ]
#         },
#         {
#             "propId": 1000,
#             "edited": [
#                 {
#                     "id": 45615,
#                     "parts": [
#                         {
#                             "part": 1,
#                             "values": [
#                                 {
#                                     "id": 59757,
#                                     "value": "3"
#                                 }
#                             ]
#                         },
#                         {
#                             "part": 2,
#                             "values": [
#                                 {
#                                     "id": 85257,
#                                     "value": "1500"
#                                 }
#                             ]
#                         },
#                         {
#                             "part": 3,
#                             "values": [
#                                 {
#                                     "id": 78957,
#                                     "value": "500"
#                                 }
#                             ]
#                         }
#                     ]
#                 },
#                 {
#                     "id": 156852,
#                     "parts": [
#                         {
#                             "part": 2,
#                             "values": [
#                                 {
#                                     "id": 79457,
#                                     "value": "2000"
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ]
#         },
#         {
#             "propId": 1004,
#             "added": [
#                 {

#                     "parts": [
#                         {
#                             "part": 1,
#                             "values": [
#                                 {
#                                     "value": "this is a test to check"
#                                 }
#                             ]
#                         },
#                         {
#                             "part": 2,
#                             "values": [
#                                 {
#                                     "value": "this is a test"
#                                 }
#                             ]
#                         }
#                     ]
#                 },
#                 {
#                     "parts": [
#                         {
#                             "part": 1,
#                             "values": [
#                                 {
#                                     "value": "0"
#                                 }
#                             ]
#                         },
#                         {
#                             "part": 2,
#                             "values": [
#                                 {
#                                     "value": "this"
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ],
#             "deleted": [
#                 {
#                     "id": 8
#                 }
#             ]
#         },
#         {
#             "propId": 1007,
#             "added": [
#                 {
#                     "id": 2,
#                     "parts": [
#                         {
#                             "part": 1,
#                             "values": [
#                                 {
#                                     "value": "this is a test to ckeck is add working or not"
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ],
#             "deleted": [
#                 {
#                     "id": 3086725,
#                     "parts": [
#                         {
#                             "part": 1,
#                             "values": [
#                                 {
#                                     "id": 10,
#                                     "value": "2222"
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ]
#         },
#         {
#             "propId": 130621,
#             "edited": [
#                 {
#                     "id": 8456215,
#                     "parts": [
#                         {
#                             "part": 1,
#                             "values": [
#                                 {
#                                     "id": 78854,
#                                     "value": "test",
#                                     "answer": {
#                                         "lid": 1,
#                                         "paramUrl": "/1164",
#                                         "schemaId": 1164,
#                                         "schemaVersion": 1.1,
#                                         "usedForId": 1423332,
#                                         "properties": [
#                                         {
#                                             "propId": 13060,
#                                             "multi": True,
#                                             "edited": [
#                                             {
#                                             "id": 8456251,
#                                             "parts": [
#                                             {
#                                                 "part": 1,
#                                                 "values": [
#                                                 {
#                                                 "id": 123,
#                                                 "value": "5"
#                                                 }
#                                                 ]
#                                             }
#                                             ]
#                                             }
#                                             ]
#                                         }
#                                         ]
#                                         }
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ]
#         },
#         {
#             "propId": 130631,
#             "edited": [
#                 {
#                     "id": 8456215,
#                     "parts": [
#                         {
#                             "part": 2,
#                             "values": [
#                                 {
#                                     "id": 85257,
#                                     "value": "1500", 
#                                 }
#                             ]
#                         }
#                     ]
#                 }
#             ]
#         }
#     ]
# }
js = {
	"lid": 1,
	"paramUrl": "/1165",
	"schemaId": 1165,
	"schemaVersion": 1.1,
	"usedForId": 1423330,
	"properties": [{
        	"propId": 11111,
        	"multi": False,
        	"edited": [{
            	"id": 1987,
            	"parts": [{
                	"part": 1,
                	"values": [{
                    	"id":123,
                    	"value": {
                        	"content": "data:image/jpeg;base64,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",
                        	"name": "sample1.jpg",
                        	"size": 4478,
                        	"type": "image/jpeg"
                    	}
                	}]
            	}]
        	}]
    	},
    	{
        	"propId": 22222,
        	"multi": False,
        	"deleted": [{
            	"id": 1785
        	}]
    	},
    	{
        	"propId": 33333,
        	"multi": False,
        	"added": [{
            	"parts": [{
                	"part": 1,
                	"values": [{
                        	"value": {
                            	"content": "data:image/jpeg;base64,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",
                            	"name": "sample.jpg",
                            	"size": 3226,
                            	"type": "image/jpeg"
                        	}
                    	},
                    	{
                        	"value": {
                            	"content": "data:image/jpeg;base64,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",
                            	"name": "sample1.jpg",
                            	"size": 4478,
                            	"type": "image/jpeg"
                        	}
                    	}
                	]
            	}]
        	}]
    	}
	]
}

async def f():
    my_object = parser.ParseAnswer(js)
    ni = await my_object.get_actions_async()
if __name__ == "__main__":
    asyncio.run(f())

# display flat of js completely 
# it returns a list