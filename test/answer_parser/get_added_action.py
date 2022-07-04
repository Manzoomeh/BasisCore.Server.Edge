import asyncio
from bclib import parser
from simple import js

async def f():
    my_object = parser.ParseAnswer(js)
    print(await my_object.get_added_actions_async(prp_id=[1004, 1007]))
if __name__ == "__main__":
    asyncio.run(f())

# display objects that their action is added
# prp_id can set as a list or int or None (if prp_id=None it returns all added actions)
# predicate also can be used
