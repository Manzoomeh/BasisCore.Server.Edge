"""Answer parser and HTML parser coverage."""
import asyncio

from bclib import parser
from bclib.parser import HtmlParserEx, ParseAnswer
from bclib.parser.answer import Answer, UserActionTypes


SAMPLE_ANSWER = {
    "schemaId": 1,
    "properties": [
        {
            "propId": 1004,
            "added": [
                {
                    "id": 10,
                    "parts": [
                        {
                            "part": 1,
                            "values": [{"id": 1, "value": "new-value"}],
                        }
                    ],
                }
            ],
        },
        {
            "propId": 1007,
            "edited": [
                {
                    "id": 20,
                    "parts": [
                        {
                            "part": 1,
                            "values": [{"id": 2, "value": "edited-value"}],
                        }
                    ],
                }
            ],
        },
    ],
}


def test_parse_answer_helper():
    answer = ParseAnswer(SAMPLE_ANSWER)
    assert isinstance(answer, Answer)


def test_get_added_actions():
    answer = Answer(SAMPLE_ANSWER, check_validation=False)
    added = asyncio.run(answer.get_added_actions_async())
    assert isinstance(added, list)
    assert len(added) >= 1


def test_get_actions_by_type():
    answer = Answer(SAMPLE_ANSWER, check_validation=False)
    edited = asyncio.run(
        answer.get_actions_async(action=UserActionTypes.EDITED)
    )
    assert isinstance(edited, list)


def test_html_parser_ex():
    p = HtmlParserEx()
    p.feed('<basis core="dbSource"><params><add name="x" value="1"/></params></basis>')
    data = p.get_dict()
    assert isinstance(data, dict)
    assert data  # non-empty parse tree
