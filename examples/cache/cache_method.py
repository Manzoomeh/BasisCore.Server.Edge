"""@app.cache() decorator on a REST handler."""
import time
from datetime import datetime

from bclib import edge
from bclib.context import RESTfulContext

options = {
    "name": "cache-method",
    "http": "localhost:9161",
    "router": "restful",
    "cache": {"type": "memory", "clean_interval": 0, "reset_interval": 0},
}

app = edge.from_options(options)


@app.restful_handler(app.get("api/data"))
@app.cache(30, "demo")
def data(_: RESTfulContext):
    print("Computing (uncached)...")
    time.sleep(0.5)
    return {
        "data": "static-data",
        "time": datetime.now().strftime("%H:%M:%S"),
    }


@app.restful_handler(app.get("api/get/:key"))
def get_data(context: RESTfulContext):
    key = context.url_segments.key
    return {"From Cache": context.dispatcher.cache_manager.get_cache(key)}


@app.restful_handler()
def home(_: RESTfulContext):
    return {"try": ["GET /api/data", "GET /api/get/demo"]}


if __name__ == "__main__":
    print("Cache method -> http://localhost:9161/api/data")
    app.listening()
