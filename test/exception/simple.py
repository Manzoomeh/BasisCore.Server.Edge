from bclib import edge

if "options" not in dir():
    options = {
        "server": "localhost:8080",
        "router": "web"
    }


app = edge.from_options(options)


@ app.web_action()
def process_default_web_action(context: edge.WebContext):
    some_value = 1/0
    return "result from process_default_web_action"


app.listening()
