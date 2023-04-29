from bclib import edge
import base64


options = {
    "endpoint": "127.0.0.1:1026",
    "router": "restful",
    "log_request": True
}

app = edge.from_options(options)


@app.restful_action()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    try:
        with open("C:/Users/Qamsari/Desktop/Photo/8.png", "rb") as image:
            payload = image.read()
        # remove blob from cms
        context.cms.form = None
        return {
            "name": "8.png",
            "mime": "image/ong",
            "payload": base64.b64encode(payload).decode('utf8'),
            "logs": [{
                "title": "rename",
                "message": "8.png"
            },
                {
                "title": "edit",
                "message": "1232"
            }]
        }

    except Exception as ex:
        print(ex)
        raise ex


# @app.restful_action()
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    # remove blob from cms
    context.cms.form = None
    return {
        "name": context.form.name,
        "mime": context.form.mime,
        "payload": context.form.payload,
        "logs": [{
            "title": "hi",
            "message": "123"
        },
            {
            "title": "hi1",
            "message": "1232"
        }]
    }


app.listening()
