from bclib import parser
import asyncio

question_api = "http://basispanel.ir/schema/freeform/E508E03C-E291-41DC-BAC2-90FED1AA0648/1B7C6CDC-49BB-4087-B6B9-464D98D889BA/fa/ایجاد دسته بندی"
input_json = {
  "lid": 1,
  "paramUrl": "/E508E03C-E291-41DC-BAC2-90FED1AA0648/1B7C6CDC-49BB-4087-B6B9-464D98D889BA/fa/ایجاد-دسته-بندی",
  "schemaId": "1B7C6CDC-49BB-4087-B6B9-464D98D889BA",
  "schemaVersion": 1.1,
  "properties": [
   {
    "propId": 1009,
    "multi": False,
    "added": [
     {
      "parts": [
       {
        "part": 1,
        "values": [
         {
          "value": "ابوالفضل"
         }
        ]
       }
      ]
     }
    ]
   },
   {
    "propId": 1010,
    "multi": False,
    "added": [
     {
      "parts": [
       {
        "part": 1,
        "values": [
         {
          "value": "عmskfskfdsjfsdfjdskfhajsfjfkskfhkslfhakljfhkjshfjkhsdfkjhjskfhjksdfjkshfkjsfjkshjkfhsdjkfhsjkfhsjkdfhjkdfhksنوان 1"
         }
        ]
       }
      ]
     }
    ]
   },
   {
    "propId": 1011,
    "multi": False,
    "added": [
     {
      "parts": [
       {
        "part": 1,
        "values": [
         {
          "value": "توضیح شماره 1"
         }
        ]
       }
      ]
     }
    ]
   },
   {
    "propId": 1012,
    "multi": False,
    "added": [
     {
      "parts": [
       {
        "part": 1,
        "values": [
         {
          "value": "dsfdsf"
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
    my_object = parser.Answer(input_json, question_api, check_validation=True)
    # await my_object.get_actions_async()
    print(await my_object.get_actions_async())
if __name__ == "__main__":
    asyncio.run(f())