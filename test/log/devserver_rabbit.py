from bclib import edge


options = {
    "http": "localhost:8080",
    "router": "restful",
    "logger": {
        "type": "schema.rabbit",
        "url": "http://localhost:8080/log-schema",
        "connection":
        {
            "url": "amqp://guest:guest@localhost:5672",
            "queue": "Test"
        }
    }
}


app = edge.from_options(options)


@app.restful_handler(
    app.get("log-schema/:schemaid")
)
def get_schema_by_id(context: edge.RESTfulContext):
    return {
        "sources": [
            {
                "data": [
                    {
                        "schemaId": context.url_segments.schemaid,
                        "paramUrl": f"/log-schema/{context.url_segments.schemaid}",
                        "schemaVersion": 1.1,
                        "lid": 2,
                        "schemaName": "test-schema",
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
                ]
            }
        ]
    }

@app.restful_handler(
    app.get("send")
)
async def process_restful_request_with_log_and_wait(context: edge.RESTfulContext):
    print("process_restful_request_with_log_and_wait")
    log_dict = {
        "data_1": "12",
        "data_2": "ok"
    }
    log_object = context.dispatcher.new_object_log(schema_name="test", **log_dict)
    print("befor log")
    await context.dispatcher.log_async(log_object)
    print("after log")
    return {
        "result": "ok from sync"
    }


app.listening()
