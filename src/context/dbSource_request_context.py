from .request_context import RequestContext
import utility


class DbSourceRequestContext(RequestContext):
    def __init__(self, request) -> None:
        super().__init__(request)
        parser = utility.BasisCoreHtmlParser()
        # print(request)
        html = request["form"]["command"]
        parser.feed(html)
        self.command = parser.element
