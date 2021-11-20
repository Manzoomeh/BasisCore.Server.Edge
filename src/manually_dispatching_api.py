import json
import time
from pathlib import Path
from context import RESTfulContext
from dispatcher import Dispatcher


with open(Path(__file__).with_name("host.json")) as options_file:
    options = json.load(options_file)

app = Dispatcher(options)


@app.restful_action(app.in_list("context.body.id", 10))
def process_basiscore_restful1(context: RESTfulContext):
    print("process_basiscore_restful1")
    return context.body


@app.restful_action(app.in_list("context.body.id", 1))
def process_basiscore_restful2(context: RESTfulContext):
    print("process_basiscore_restful2")
    return context.body


p = {
    "cms": {
        "request": {
            ":method": "POST",
            "methode": "post",
            ":path": "/api2/authorization/82FD3FFD-7B27-40CA-A7BE-4465A9F2AEB2/set-active",
            "rawurl": "api2/authorization/82FD3FFD-7B27-40CA-A7BE-4465A9F2AEB2/set-active",
            "url": "api2/authorization/82FD3FFD-7B27-40CA-A7BE-4465A9F2AEB2/set-active",
            ":authority": "trust-login.com",
            "full-url": "trust-login.com/api2/authorization/82FD3FFD-7B27-40CA-A7BE-4465A9F2AEB2/set-active",
            "host": "trust-login.com",
            ":scheme": "https",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0",
            "accept": "/",
            "accept-language": "en-US,en;q=0.5",
            "referer": "https://basispanel.ir/",
            "content-type": "application/json",
            "origin": "https://basispanel.ir",
            "content-length": "27",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "pragma": "no-cache",
            "cache-control": "no-cache",
            "te": "trailers",
            "accept-encoding": "br, gzip, deflate",
            "request-id": "336637",
            "hostip": "185.44.36.194",
            "hostport": "443",
            "clientip": "94.139.174.170",
            "body": "{\u0022type\u0022:\u0022corporate\u0022,\u0022id\u0022:1}"
        },
        "cms": {
            "date": "11/17/2021",
            "time": "15:57",
            "date2": "20211117",
            "time2": "155740",
            "date3": "2021.11.17"
        }
    }
}

restful_context = RESTfulContext(p["cms"], options)
result = app.dispatch(restful_context)
print(result)

# print(globals()["RESTfulContext"])