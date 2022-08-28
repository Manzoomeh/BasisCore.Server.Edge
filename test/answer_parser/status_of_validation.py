from bclib import parser
from answer_parser.validations_test import question_api, input_json
import asyncio

async def f():
    my_object = parser.Answer(input_json, question_api, check_validation=True)
    # await my_object.get_actions_async()
    print(await my_object.is_valid_answer_async())
if __name__ == "__main__":
    asyncio.run(f())