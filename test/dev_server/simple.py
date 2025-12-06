from bclib import edge

if "options" not in dir():
    options = {
        "http": "localhost:8080",
        "router": "web"
    }


app = edge.from_options(options)


async def check_async(context: edge.RequestContext):
    return context.url.endswith("app")


@app.web_handler(app.callback(check_async))
def process_web_handler(context: edge.HttpContext):
    return "result from process_web_handler"


@app.web_handler()
def process_default_web_handler(context: edge.HttpContext):
    return "result from process_default_web_handler"


app.listening()
