from bclib import edge

if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "web"
    }


app = edge.from_options(options)


async def check_async(context: edge.RequestContext):
    return context.url.endswith("app")


@app.web_action(app.callback(check_async))
def process_web_action(context: edge.WebContext):
    return "result from process_web_action"


@app.web_action()
def process_default_web_action(context: edge.WebContext):
    return "result from process_default_web_action"


app.listening()
