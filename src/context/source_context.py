from utility import BasisCoreHtmlParser
from utility.DictEx import DictEx
from .request_context import RequestContext


class SourceContext(RequestContext):
    """Context for dbSource request"""

    def __init__(self, request) -> None:
        super().__init__(request)
        parser = BasisCoreHtmlParser()
        html = self.request.form.command
        parser.feed(html)
        self.__command = parser.get_dict_ex()
        self.process_async = True

    @property
    def command(self) -> DictEx:
        return self.__command
