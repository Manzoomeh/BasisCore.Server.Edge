import datetime
import json
import xml.etree.ElementTree

import edge

options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "router": {
        "client_source": ["/source"],
        "restful": ["/rest"],
        "web": ["*"],
    }
}

app = edge.from_options(options)

app.cache()


def generate_data() -> list:
    import random  # define the random module
    import string

    ret_val = list()
    for i in range(10):
        ret_val.append({"id": i, "data": ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))})
    return ret_val


###########################################
# rest
###########################################


@app.restful_handler(
    app.url("qam-test/rest/:id"))
def process_restful_with_filter_request(context: edge.RESTfulContext):
    print("process_restful_with_filter_request")
    id = int(context.url_segments.id)
    return [row for row in generate_data() if row["id"] == id]


@app.restful_handler(
    app.url("qam-test/rest"))
def process_restful_request(context: edge.RESTfulContext):
    print("process_restful_request")
    return generate_data()


######################
# source
######################


@app.client_source_handler(
    app.equal("context.command.source", "basiscore"),
    app.in_list("context.command.mid", "10", "20"))
def process_basiscore_source(context: edge.ClientSourceContext):
    print("process_basiscore_source")
    return generate_data()


@app.client_source_handler(
    app.equal("context.command.source", "demo"),
    app.in_list("context.command.mid", "10", "20"))
def process_demo_source(context: edge.ClientSourceContext):
    return [row for row in generate_data() if row["id"] < 5]


@app.client_source_member_handler(
    app.equal("context.member.name", "list")
)
def process_list_member(context: edge.ClientSourceMemberContext):
    print("process_list_member")
    return context.data


@app.client_source_member_handler(
    app.equal("context.member.name", "paging")
)
def process_page_member(context: edge.ClientSourceMemberContext):
    data = {
        "total": len(context.data),
        "from": 0,
        "to": len(context.data)-1,
    }
    print("process_page_member")
    return data


@app.client_source_member_handler(
    app.equal("context.member.name", "count")
)
def process_count_member(context: edge.ClientSourceMemberContext):
    data = {
        "count": len(context.data)
    }
    print("process_count_member")
    return data

########
# Socket
########


class Client:

    def __init__(self, sessionId: str, cms: edge.DictEx):
        self.cms = cms
        self.SessionId = sessionId
        self.UserName = None

    def update(self, message: edge.DictEx):
        command = xml.etree.ElementTree.fromstring(message.command)
        if self.UserName == None:
            self.UserName = command.get('user-name')
            if (self.UserName == "."):
                self.close(True)
            else:
                ChatRoom.send_to_all_message(
                    None, f'{self.UserName} Connected!', 'system')
                print(f'{self.UserName} with id {self.SessionId} connected')
        else:
            userMessage = command.get("message")
            if userMessage == 'end':
                self.close(True)
            else:
                print(f'{self.UserName} Say: {userMessage}')
                ChatRoom.send_to_all_message(
                    self.UserName, userMessage, 'user')

    def close(self, fromServer):
        if fromServer == True:
            app.send_message(edge.Message.create_disconnect(self.SessionId))

        ChatRoom.send_to_all_message(
            None, f"{self.UserName} Disconnected!", 'system')
        print(f'{self.UserName} Disconnected')


class ChatRoom:

    __sessions: 'dict[str, Client]' = {}

    @staticmethod
    def send_to_all_message(owner: str, message: str, msg_category: str):
        messageTime = datetime.datetime.now().strftime('%H:%M:%S')
        data = {
            "_": {
                "Replace": False
            },
            "data": [["Type", "Owner", "Time", "Message"],
                     [msg_category, owner, messageTime, message]]
        }
        msg = json.dumps(data)
        for session_id, _ in ChatRoom.__sessions.items():
            app.send_message(edge.Message.create_from_text(session_id, msg))

    @staticmethod
    def process_message(message: edge.Message, cms: edge.DictEx, body: edge.DictEx):
        if (message.type == edge.MessageType.CONNECT):
            ChatRoom.__sessions[message.session_id] = Client(
                message.session_id, cms)
        elif message.type == edge.MessageType.DISCONNECT:
            if message.session_id in ChatRoom.__sessions:
                ChatRoom.__sessions[message.session_id].close(False)
                del ChatRoom.__sessions[message.session_id]
        elif message.type == edge.MessageType.MESSAGE:
            if message.session_id in ChatRoom.__sessions:
                ChatRoom.__sessions[message.session_id].update(body)
        elif message.type == edge.MessageType.NOT_EXIST:
            if message.session_id in ChatRoom.__sessions:
                del ChatRoom.__sessions[message.session_id]
        elif message.type == edge.MessageType.AD_HOC:
            if message.session_id in ChatRoom.__sessions:
                print("adhoc message receive!")


@app.socket_action(app.equal("context.message_type", edge.MessageType.NOT_EXIST))
def process_not_exist_message(context: edge.SocketContext):
    print("process_not_exist_message")
    ChatRoom.process_message(context.message, None, None)


@app.socket_action()
def process_all_other_message(context: edge.SocketContext):
    print("process_all_other_message")
    ChatRoom.process_message(context.message,
                             context.cms, context.body)


#####
# Web
#####
@app.web_handler(app.url("qam-test/chat"))
def process_web_message(context: edge.HttpContext):
    return """
            <style>
            td {
                border-color: black;
                border-width: 1px;
                border-style: solid;
            }

            .owner {
                color: green;
            }
            .time {
                font-size: smaller;
                color: lightcoral;
                font-weight: normal;
            }
            .sys-message {
                font-style: italic;
                font-weight: bold;
                color: gray;
            }
            [data-message-list] {
                list-style: none;
                padding: 0px;
            }
            </style>
            <script>
            var host = {
                Debug: false,
                DbLibPath: "https://cdn.basiscore.net/_js/alasql.min.js",
                Settings: {
                "connection.websocket.simplechat": "ws://127.0.0.1:1030/chat",

                "default.source.verb": "get",
                "default.call.verb": "get",
                "default.viewCommand.groupColumn": "prpid",
                "default.binding.regex": "\\{##([^#]*)##\\}",
                },
            };
            </script>
       
            <div>
            <div style="display: none" data-code>
                <basis
                core="print"
                run="atclient"
                renderto="[data-app]"
                if="!{##app.local##}"
                >
                <layout>
                    <script type="text/template">
                    <label>UserName</label>
                    <input id="user-name" />
                    <input type="button" onclick="TryLoginAsync()" value="login" />
                    </script>
                </layout>
                </basis>
                <basis
                core="print"
                run="atclient"
                renderto="[data-app]"
                if="{##app.local##}"
                >
                <layout>
                    <script type="text/template">

                    <div>
                        <div style="overflow-y:scroll;height:200px">
                            <ul data-message-list></ul>
                        </div>

                        <input id="message" />
                        <input type="button" onclick="TrySendMessageAsync()" value="Send" />
                        <input type="button" onclick="TryLogoutAsync()" value="Logout {##app.local.user-name##}" />
                    </div>
                    </script>
                </layout>
                </basis>

                <basis
                core="dbsource"
                source="simplechat"
                name="chat"
                run="atclient"
                renderto="*"
                user-name="{##app.local.user-name|(.)##}"
                if="{##app.local##}"
                >
                <member name="message" />
                </basis>
                <Basis
                core="print"
                datamembername="chat.message"
                run="atclient"
                renderto="[data-message-list]"
                if="{##app.local##}"
                >
                <layout>
                    <script type="text/template">
                    @child
                    </script>
                </layout>
                <face filter="type ='user'">
                    <script type="text/template">
                    <li class="user-message">
                        <span class="time">@time</span>
                        <span class="owner">@owner</span>:
                        <span class="message">@message</span>
                    </li>
                    </script>
                </face>
                <face filter="type ='system'">
                    <script type="text/template">
                    <li class="sys-message">
                        <span class="time">@time</span>
                        <span class="message">@message</span>
                    </li>
                    </script>
                </face>
                </Basis>
            </div>
            </div>
            <div data-app></div>

            <script src="https://cdn.basiscore.net/_js/basiscore-1.6.min.js"></script>
            <script>
            async function TryLoginAsync() {
                var userName = document.getElementById("user-name").value;
                await $bc().AddObjectAsync({ "user-name": userName }, "app.local");
                await $bc().RenderAsync("[data-code]");
            }

            async function TrySendMessageAsync() {
                var input = document.getElementById("message");
                var message = document.getElementById("message").value;
                var element = document.querySelector('basis[core="dbsource"]');
                element.setAttribute("message", message);
                await $bc().GetCommand(element).UpdateAsync();
                element.removeAttribute("message");
                input.value = "";
            }

            async function TryLogoutAsync() {
                $bc().TryRemoveDataSource("app.local");
                await $bc().RenderAsync("[data-code]");
            }
            </script>
        """


@app.web_handler(
    app.url("qam-test/sample-source/:source"),
    app.in_list("context.url_segments.source", "demo", "basiscore"))
def process_web_sample_source_request(context: edge.HttpContext):
    return f"""
     <basis core="dbsource" run="atclient" source="{context.url_segments.source}" mid="20" name="demo"  lid="1" dmnid="" ownerpermit="" >
        <member name="list" type="list" pageno="3" perpage="20" request="catname" order="id desc"></member>
        <member name="paging" type="list" request="paging" count="5" parentname="list"></member>
        <member name="count" type="scalar" request="count" ></member>
     </basis>

    <basis core="callback" run="AtClient" triggers="demo.list demo.paging demo.count" method="onSource"></basis>
<h1>Press F12 for visit result in console</h1>
    <script>
        var host = {{
            debug: false,
            autoRender: true,
            'DbLibPath': '/alasql.min.js',
            settings: {{
                'connection.web.{context.url_segments.source}': 'http://localhost:1564/qam-test/source',
                
                'default.dmnid': 2668,
            }},

        }}


        function onSource(args) {{
            console.table(args.source.rows);
        }}
    </script>
    <script src="https://cdn.basiscore.net/_js/basiscore-2.4.11.min.js"></script>
        """


@app.web_handler()
def process_web_remain_request(context: edge.HttpContext):
    print("process_web_remain_request")
    context.add_header(edge.HttpHeaders.ACCESS_CONTROL_ALLOW_ORIGIN, "*")
    context.add_header("x-ali", "12")
    return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta http-equiv="X-UA-Compatible" content="IE=edge" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>Edge Sample page</title>
        </head>
        <body>
            <h1 style="text-align: center">
            hello world from Edge
            <img
                src=" data:image/png;base64,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"
                style="vertical-align: middle"
            />
            over socket
            </h1>
            <ul>
            <li>
                RESTful
                <ul>
                <li>
                    <a href="http://localhost:1564/qam-test/rest" target="_blank"
                    >Simple</a
                    >
                </li>
                <li>
                    <a href="http://localhost:1564/qam-test/rest/5" target="_blank"
                    >With param</a
                    >
                </li>
                </ul>
            </li>
            <li>
                Socket
                <ul>
                    <li>
                        <a href="http://localhost:1564/qam-test/chat" target="_blank"
                        >Chat</a
                    >
                    </li>
                </ul>
            </li>
            <li>
                DbSource
                <ul>
                    <li> <a href="http://localhost:1564/qam-test/sample-source/basiscore" target="_blank"
                        >Sample 1</a
                    ></li>
                    <li> <a href="http://localhost:1564/qam-test/sample-source/demo" target="_blank"
                        >Sample 2</a
                    ></li>
                </ul>
            </li>
            </ul>
        </body>
        </html>
            """


app.listening()
