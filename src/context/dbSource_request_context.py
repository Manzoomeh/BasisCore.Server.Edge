from .request_context import RequestContext
import utility


class DbSourceRequestContext(RequestContext):
    def __init__(self, request) -> None:
        super().__init__(request)
        parser = utility.BasisCoreHtmlParser()
        html = request["form"]["command"]
        parser.feed(html)
        self.command = parser.element
