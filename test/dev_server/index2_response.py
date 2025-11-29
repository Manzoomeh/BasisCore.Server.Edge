from bclib import edge


options = {
    "server": "localhost:8080",
    "router": "restful"
}

app = edge.from_options(options)

@app.restful_handler(
    app.url("test")
)
def process_send_file(context: edge.RESTfulContext):
    edge.HttpHeaders.add_cors_headers(context)
    context.response_type = edge.ResponseTypes.STATIC_FILE
    context.mime = edge.HttpMimeTypes.CSS
    cms = context.cms
    if edge.HttpBaseDataType.CMS not in cms:
        cms[edge.HttpBaseDataType.CMS] = dict()
    cms_cms = cms[edge.HttpBaseDataType.CMS]
    if edge.HttpBaseDataType.WEB_SERVER not in cms_cms:
        cms_cms[edge.HttpBaseDataType.WEB_SERVER] = dict()
    cms_cms[edge.HttpBaseDataType.WEB_SERVER][edge.HttpBaseDataName.FILE_PATH] = "C:\\Users\\t2\\Desktop\\test.css"
    return context.cms

app.listening()