from bclib import edge


options = {
    "server": "localhost:8080",
    "router": "restful",
    "logger": {
        "type": "schema",
        "url": "http://localhost:8080/log-schema"
    }
}


app = edge.from_options(options)


@app.restful_action(app.get("log-schema"))
def get_schema_by_id(context: edge.RESTfulContext):
    return {
        "schemaId": 1161,
        "schemaVersion": 1.1,
        "lid": 2,
        "name": "test-schema",
        "questions": [
            {
                "prpId": 13050,
                "title": "data_1",
                "parts": [
                    {
                        "part": 1,
                        "viewType": "text"
                    }
                ]
            },
            {
                "prpId": 13051,
                "title": "data_2",
                "parts": [
                    {
                        "part": 1,
                        "viewType": "text"
                    }
                ]
            },
            {
                "prpId": 13052,
                "title": "data_3",
                "parts": [
                    {
                        "part": 1,
                        "viewType": "text"
                    }
                ]
            },
            {
                "prpId": 13053,
                "title": "url",
                "source": "context.cms.request.url",
                "parts": [
                    {
                        "part": 1,
                        "viewType": "text"
                    }
                ]
            }
        ],
    }


@app.restful_action(app.post("log-schema"))
def save_schema(context: edge.RESTfulContext):
    print("must be save", context.body.schema)


@app.restful_action()
async def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    data_1 = 12
    data_2 = "ok"
    await context.dispatcher.log_async(**locals(), data_3="333", schema_id=1161)
    return {"result": "ok"}


app.listening()