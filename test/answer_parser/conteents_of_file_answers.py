import asyncio
from bclib import parser
from file_answers import js

async def f():
    my_object = parser.ParseAnswer(js)
    part = (await my_object.get_actions_async(is_file=True))[0]
    # print(part.as_file_content())
    print(part.as_file_content().size)

asyncio.run(f())

# display file view of prp that is a file
# it is an object and you can access to its attrs such as size, mime, prp_id and etc by . 