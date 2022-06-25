import asyncio
from bclib import parser
from simple import js

async def f():
    my_object = parser.ParseAnswer(js)
    print(await my_object.get_actions_async(predicate=lambda x: x.prp_id ==12345 or x.action == parser.UserActionTypes.DELETED))

if __name__ == "__main__":
    asyncio.run(f())

# hint of using predicate