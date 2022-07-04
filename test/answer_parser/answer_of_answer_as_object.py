import asyncio
from bclib import parser
from simple import js

async def f():
    my_object = parser.ParseAnswer(js)
    part = await my_object.get_actions_async(prp_id = 130621)
    print(part)

asyncio.run(f())

# display prp that have an answer 
# its answer displayed as an object of Answer Class