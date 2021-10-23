from html.parser import HTMLParser
from .HtmlTag import HtmlTag


class BasisCoreHtmlParser(HTMLParser):
    def __init__(self,) -> None:
        super().__init__()
        self.element = None
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if(self.element != None):
            self.stack.append(self.element)

        self.element = HtmlTag(tag)
        for name, value in attrs:
            self.element.attributes[name] = value
        #print("Encountered a start tag:", tag, self.element.attributes)

    def handle_endtag(self, tag):
        if(len(self.stack) != 0):
            tmp = self.element
            self.element = self.stack.pop()
            self.element.childList.append(tmp)
        #print("Encountered an end tag :", tag)

    def handle_data(self, data):
        #print("Encountered some data  :", data)
        pass
