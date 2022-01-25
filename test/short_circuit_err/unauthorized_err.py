from bclib import edge

if "options" not in dir():
    options = {
        "server": {
            "ip": "localhost",
            "port": 1020,
        },
        "router": "web"
    }


app = edge.from_options(options)


def check_url(context: edge.WebContext) -> bool:
    if context.url.endswith('error'):
        raise edge.UnauthorizedErr("Custom Unauthorize message")
    return True


@app.web_action(app.callback(lambda x: x.url.startswith('app')), app.callback(check_url))
def process_web_action(context: edge.WebContext):
    return "result from process_web_action"


@ app.web_action()
def process_default_web_action(context: edge.WebContext):
    return "result from process_default_web_action"


app.listening()
