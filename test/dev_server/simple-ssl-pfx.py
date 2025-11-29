from bclib import edge

if "options" not in dir():
    options = {
        "server": "localhost:8081",
        "router": "web",
        "ssl": {
            "pfxfile": "D:/Programming/Falsafi/BasisCore/Server/BasisCore.Server.Edge/test/test-cert/server.pfx",
            "password": "1234"
        }
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
