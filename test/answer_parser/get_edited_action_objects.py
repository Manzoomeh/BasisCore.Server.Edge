import asyncio
from bclib import parser
from simple import js

async def f():
    my_object = parser.ParseAnswer(js)
    print(await my_object.get_edited_actions_async(prp_id=130631))
if __name__ == "__main__":
    asyncio.run(f())

# display objects that their action is edited
# prp_id can set as a list or int or None (if prp_id=None it returns all added actions)
# predicate also can be used
