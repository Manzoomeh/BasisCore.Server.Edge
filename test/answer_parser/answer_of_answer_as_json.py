import asyncio
from bclib import parser
from simple import js

async def f():
    my_object = parser.ParseAnswer(js)
    parts = await my_object.get_actions_async()
    k = dict()
    for part in parts:
        if part.answer:
            k[part.value] = part.answer.json
    print(k)

asyncio.run(f())

# display value and answer of a part if this part have an answer
# answer is an object of Answer class so it has attrs of this class such as json field