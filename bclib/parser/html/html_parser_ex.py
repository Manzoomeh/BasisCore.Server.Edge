"""import html parser"""
from html.parser import HTMLParser
from typing import Any
from bclib.utility import DictEx
from ..html.html_tag import HtmlTag


class HtmlParserEx(HTMLParser):
    """custom parser for row html"""

    def __init__(self,) -> None:
        super().__init__()
        self.element = None
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if self.element is not None:
            self.stack.append(self.element)

        self.element = HtmlTag(tag)
        for name, value in attrs:
            self.element.attributes[name] = value

    def handle_endtag(self, tag):
        if len(self.stack) != 0:
            tmp = self.element
            self.element = self.stack.pop()
            self.element.child_list.append(tmp)

    def handle_data(self, data):
        pass

    def error(self, message: str) -> Any:
        print("Error in parse html", message)
        return super().error(message)

    def get_dict_ex(self) -> DictEx:
        def _convert_tag_to_dict(tag: HtmlTag) -> dict:
            dic = dict(tag.attributes)
            for child in tag.child_list:
                if child.name in dic:
                    dic_list = dic.get(child.name)
                else:
                    dic_list = dic[child.name] = list()
                child_dict = _convert_tag_to_dict(child)
                dic_list.append(child_dict)
            return dic
        new_dic = _convert_tag_to_dict(self.element)
        return DictEx(new_dic)
