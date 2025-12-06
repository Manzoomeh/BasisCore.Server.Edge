import asyncio
from bclib import edge


options = {
    "http": "localhost:8080",
    "router": "restful",
    "log_request": False
}

app = edge.from_options(options)

data = list()

async def load_data_async() -> list:
    import string
    import random
    for i in range(10):
        data.append({"id": i, "data": ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))})
        await asyncio.sleep(.1)
    print("data loaded!")
    return data


@app.restful_handler(
    app.url(":id"))
def process_restful_with_filter_request(context: edge.RESTfulContext):
    print("process_restful_with_filter_request")
    id = int(context.url_segments.id)
    return [row for row in data if row["id"] == id]


@app.restful_handler()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    return load_data_async()


async def initialize_process_async():
    print("Initialize resources...")
    await load_data_async()

async def dispose_process_async():
    print("Dispose resources...")
    await asyncio.sleep(.1)

app.listening(before_start=initialize_process_async,after_end= dispose_process_async)
