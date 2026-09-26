import asyncio

from bclib import parser

try:
    from simple import js
except ImportError:
    from examples.parser.answer.simple import js


async def f():
    my_object = parser.ParseAnswer(js)
    print(await my_object.get_added_actions_async(prp_id=[1004, 1007]))


if __name__ == "__main__":
    asyncio.run(f())
