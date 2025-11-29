from bclib import edge

options = {
    "server": "localhost:8080",
    "router": "restful",
    "logger": {
        "type": "schema.rabbit",
        "url": "http://localhost:8080/log-schema",
        "connection":
        {
            "url": "amqp://guest:guest@localhost:5672",
            "queue": "hello"
        }
    }
}

app = edge.from_options(options)

@app.restful_handler(app.url("log-schema/hashid"))
def process_questions(context: edge.RESTfulContext):
    return {
        "setting": {
            "keepalive": True
        }, 
        "sources": [
            {
                "options": {
                    "tableName": "answer.data", 
                    "keyFieldName": "", 
                    "statusFieldName": "", 
                    "mergeType": 0
                }, 
            "data": [
                {
                    "schemaId": "", 
                    "paramUrl": "", 
                    "schemaName": "Test-Schema", 
                    "schemaVersion": "1.0.0", 
                    "lid": 2, 
                    "questions": [
                        {
                            "prpId": 5664, 
                            "wordId": 178, 
                            "title": "dmnid", 
                            "multi": False, 
                            "TypeID": 136, 
                            "parts": [
                                {
                                    "viewType": "text", 
                                    "part": 1, 
                                    "validations": {
                                        "required": True, 
                                        "dataType": "int"
                                    }
                                }
                            ]
                        }, 
                        {
                            "prpId": 5665, 
                            "wordId": 177, 
                            "title": "owner", 
                            "multi": False, 
                            "TypeID": 130, 
                            "parts": [
                                {
                                    "viewType": "text", 
                                    "part": 1, 
                                    "validations": {
                                        "required": True, 
                                        "dataType": "int"
                                    }
                                },
                                {
                                    "viewType": "text",
                                    "part": 2,
                                    "validations": {
                                        "required": True
                                    } 
                                }
                            ]
                        },
                        {
                            "prpId": 6259, 
                            "wordId": 176, 
                            "title": "userid", 
                            "multi": False, 
                            "parts": [
                                {
                                    "viewType": "text", 
                                    "part": 1, 
                                    "validations": {
                                        "dataType": "int"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
}

@app.restful_handler(app.url("old-version"))
async def process_create_log(context: edge.RESTfulContext):
    await context.dispatcher.log_async(
        **{
            "dmnid": 30,
            "schema_name": "hashid"
        }
    )

@app.restful_handler(app.url("new-version"))
async def process_create_log(context: edge.RESTfulContext):
    log_obj = context.dispatcher.new_object_log(
        **{
            "dmnid": 30,
            "schema_name": "hashid"
        }
    )
    log_obj.add_property("dmnid", [40, "Should not be present in log"])
    log_obj.add_property("owner", [1, "ManzoomehNegaran"])
    log_obj.add_property("owner", [1000, "ManzoomehNegaran1"])
    log_obj.add_property("usesrid", [])
    await context.dispatcher.log_async(log_object=log_obj)


app.listening()