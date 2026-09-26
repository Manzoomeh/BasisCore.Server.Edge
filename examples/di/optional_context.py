"""Optional context — handlers may omit context and still get DI."""
from abc import ABC, abstractmethod
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext


class IClock(ABC):
    @abstractmethod
    def now(self) -> str:
        ...


class Clock(IClock):
    def now(self) -> str:
        return datetime.now().isoformat(timespec="seconds")


app = edge.from_options({
    "name": "di-optional-context",
    "http": "localhost:9103",
    "router": "restful",
})

app.service_provider.add_singleton(IClock, Clock)


@app.restful_handler("api/with-context", method="GET")
def with_context(context: RESTfulContext, clock: IClock):
    return {"url": context.url, "now": clock.now()}


@app.restful_handler("api/no-context", method="GET")
def no_context(clock: IClock):
    return {"now": clock.now(), "note": "no context param"}


if __name__ == "__main__":
    print("Optional context -> http://localhost:9103/api/no-context")
    app.listening()
