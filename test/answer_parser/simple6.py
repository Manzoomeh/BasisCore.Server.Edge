import asyncio
from bclib import parser
from simple import js

async def f():
    my_object = parser.ParseAnswer(js)
    print(await my_object.get_actions_async(action=[parser.UserActionTypes.EDITED, parser.UserActionTypes.ADDED], part=[1, 2]))

if __name__ == "__main__":
    asyncio.run(f())

# parameters of functions can be a list of params