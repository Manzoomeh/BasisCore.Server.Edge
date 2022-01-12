class HtmlTag():
    def __init__(self, tag: str) -> None:
        self.name = tag
        self.attributes: dict(str, str) = dict()
        self.child_list: list[HtmlTag] = list()
