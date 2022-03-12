import json
import datetime
import xml.etree.ElementTree
from bclib import edge


options = {
    "sender": "127.0.0.1:1025",
    "receiver": "127.0.0.1:1026",
    "defaultRouter": "server_source",
    "router": "web"
}

app = edge.from_options(options)


class Client:

    def __init__(self, session_id: str, cms: edge.DictEx):
        self.cms = cms
        self.session_id = session_id
        self.user_name = None

    async def update_async(self, message: edge.DictEx):
        command = xml.etree.ElementTree.fromstring(message.command)
        if self.user_name == None:
            self.user_name = command.get('user-name')
            if(self.user_name == "."):
                self.close_async(True)
            else:
                await ChatRoom.send_to_all_message_async(
                    None, f'{self.user_name} Connected!', 'system')
                print(f'{self.user_name} with id {self.session_id} connected')
        else:
            user_message = command.get("message")
            if user_message == 'end':
                self.close_async(True)
            else:
                print(f'{self.user_name} Say: {user_message}')
                await ChatRoom.send_to_all_message_async(
                    self.user_name, user_message, 'user')

    async def close_async(self, from_server):
        if from_server == True:
            await app.send_message_async(edge.Message.create_disconnect(self.session_id))

        await ChatRoom.send_to_all_message_async(
            None, f"{self.user_name} Disconnected!", 'system')
        print(f'{self.user_name} Disconnected')


class ChatRoom:

    __sessions: 'dict[str, Client]' = {}

    @staticmethod
    async def send_to_all_message_async(owner: str, message: str, msg_category: str):
        message_time = datetime.datetime.now().strftime('%H:%M:%S')
        data = {
            "_": {
                "Replace": False
            },
            "data": [["Type", "Owner", "Time", "Message"],
                     [msg_category, owner, message_time, message]]
        }
        msg = json.dumps(data)
        for session_id, _ in ChatRoom.__sessions.items():
            await app.send_message_async(
                edge.Message.create_from_text(session_id, msg))

    @staticmethod
    async def process_message_async(message: edge.Message, cms: edge.DictEx, body: edge.DictEx):
        if(message.type == edge.MessageType.CONNECT):
            ChatRoom.__sessions[message.session_id] = Client(
                message.session_id, cms)
        elif message.type == edge.MessageType.DISCONNECT:
            if message.session_id in ChatRoom.__sessions:
                await ChatRoom.__sessions[message.session_id].close_async(False)
                del ChatRoom.__sessions[message.session_id]
        elif message.type == edge.MessageType.MESSAGE:
            if message.session_id in ChatRoom.__sessions:
                await ChatRoom.__sessions[message.session_id].update_async(body)
        elif message.type == edge.MessageType.NOT_EXIST:
            if message.session_id in ChatRoom.__sessions:
                del ChatRoom.__sessions[message.session_id]
        elif message.type == edge.MessageType.AD_HOC:
            if message.session_id in ChatRoom.__sessions:
                print("adhoc message receive!")
########
# Socket
########


@app.socket_action(app.equal("context.message_type", edge.MessageType.NOT_EXIST))
async def process_not_exist_message_async(context: edge.SocketContext):
    print("process_not_exist_message")
    await ChatRoom.process_message_async(context.message_object, None, None)


@ app.socket_action()
async def process_all_other_message_async(context: edge.SocketContext):
    print("process_all_other_message")
    await ChatRoom.process_message_async(context.message_object,
                                         context.cms, context.body)


#####
# Web
#####
@app.web_action()
def process_web_message(context: edge.WebContext):
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


app.listening()
