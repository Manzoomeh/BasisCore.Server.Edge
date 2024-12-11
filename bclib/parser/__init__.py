from typing import Any
from bclib.parser.html.html_parser_ex import HtmlParserEx
from bclib.parser.answer import Answer, UserActionTypes, UserAction


def ParseAnswer(json: 'str|Any') -> 'Answer':
    return Answer(json)
