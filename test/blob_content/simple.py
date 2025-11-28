import os

from bclib import edge

options = {
    "endpoint": "127.0.0.1:1025",
    "router":  "web"
}

app = edge.from_options(options)


@app.web_action(app.get("xlsx"))
async def process_web_remain_request(context: edge.HttpContext):
    print("xlsx")
    context.mime = edge.HttpMimeTypes.XLSX
    path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "sample.xlsx")
    with open(path, "rb") as f:
        return f.read()


@app.web_action()
async def process_web_remain_request(context: edge.HttpContext):
    print("all")
    return """
        <form method="post" enctype="multipart/form-data">
<input type="file" name="my_files" multiple="multiple"/>
<input type="submit"/>
</form>
            """
app.listening()
