class HtmlTag():
    def __init__(self, tag: str) -> None:
        self.name = tag
        self.attributes = dict()
        self.child_list = list()
