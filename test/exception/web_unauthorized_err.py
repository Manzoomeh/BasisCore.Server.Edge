from bclib import edge

if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "web"
    }


app = edge.from_options(options)


async def check_url(context: edge.WebContext) -> bool:
    if context.url.endswith('error'):
        raise edge.UnauthorizedErr("Custom Unauthorize message")
    return True


async def simple_check_url(context: edge.WebContext) -> bool:
    return context.url.startswith('app')


@app.web_action(app.callback(simple_check_url), app.callback(check_url))
def process_web_action(context: edge.WebContext):
    return "result from process_web_action"


@ app.web_action()
def process_default_web_action(context: edge.WebContext):
    return "result from process_default_web_action"


app.listening()
