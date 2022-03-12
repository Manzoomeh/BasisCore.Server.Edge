
from bclib import edge


options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "router":  "web"
}

app = edge.from_options(options)


@ app.web_action()
def process_web_remain_request(context: edge.WebContext):
    print("process_web_remain_request")
    return """
        <form method="post" enctype="multipart/form-data">
<input type="file" name="my_files" multiple="multiple"/>
<input type="submit"/>
</form>
            """


app.listening()
