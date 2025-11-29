from bclib import edge

if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "web"
    }


app = edge.from_options(options)


async def check_url(context: edge.HttpContext) -> bool:
    if context.url.endswith('error'):
        raise edge.UnauthorizedErr("Custom Unauthorize message")
    return True


async def simple_check_url(context: edge.HttpContext) -> bool:
    return context.url.startswith('app')


@app.web_handler(app.callback(simple_check_url), app.callback(check_url))
def process_web_handler(context: edge.HttpContext):
    return "result from process_web_handler"


@app.web_handler()
def process_default_web_handler(context: edge.HttpContext):
    return "result from process_default_web_handler"


app.listening()
