import asyncio
from bclib import parser
from simple import js

async def f():
    my_object = parser.ParseAnswer(js)
    part = await my_object.get_actions_async(prp_id = 130621, part=1)
    answer = part[0].answer
    print(await answer.get_actions_async())
asyncio.run(f())

# display answer of a prp as flat