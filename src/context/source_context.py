from utility import BasisCoreHtmlParser
from .context import Context


class SourceContext(Context):
    """Context for dbSource request"""

    def __init__(self, request) -> None:
        super().__init__(request)
        parser = BasisCoreHtmlParser()
        html = self.request.form.command
        parser.feed(html)
        self.command = parser.element
        self.process_async = True
