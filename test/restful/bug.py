from bclib import edge


options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "router": "restful"
}

app = edge.from_options(options)


@app.restful_handler()
def sabt_document(context: edge.RESTfulContext):
    print('end')
    return {"data": "isOk"}


app.listening()
