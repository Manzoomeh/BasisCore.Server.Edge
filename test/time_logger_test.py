from bclib import edge

options = {
    "server": "localhost:8080",
    "router": "restful",
    "log_error": True,
    "log_request": True,
    "time_logger": {
        "type": "file",
        "file_path": ["test.txt", "test2.txt", "./test/test3.json"],
        "critical_time": 0
    }
}

app = edge.from_options(options)

import time
import random

@app.restful_action()
def salam(context: edge.RESTfulContext):
    random_number = 2
    # random_number = 10 * random.random()
    data = dict()
    for i in range(1000):
        data.update({
            f"number{i}": i
        })
    return data

app.listening()