"""Simple DI example — register services and inject into REST handlers."""
from abc import ABC, abstractmethod
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext


class IGreeter(ABC):
    @abstractmethod
    def greet(self, name: str) -> str:
        ...


class Greeter(IGreeter):
    def greet(self, name: str) -> str:
        return f"Hello, {name}! ({datetime.now():%H:%M:%S})"


app = edge.from_options({
    "name": "di-simple",
    "http": "localhost:9101",
    "router": "restful",
})

app.service_provider.add_singleton(IGreeter, Greeter)


@app.restful_handler("api/greet/:name", method="GET")
def greet(context: RESTfulContext, greeter: IGreeter):
    return {
        "text": greeter.greet(context.url_segments["name"]),
        "path": context.url,
    }


@app.restful_handler("api/health", method="GET")
def health():
    return {"ok": True}


if __name__ == "__main__":
    print("DI simple -> http://localhost:9101/api/greet/Ada")
    app.listening()
