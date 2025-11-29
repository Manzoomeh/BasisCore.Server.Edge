import datetime
import json
import os
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
        if self.user_name:
            user_message = command.get("message")
            if user_message == 'end':
                self.close_async(True)
            else:
                print(f'{self.user_name} Say: {user_message}')
                await ChatRoom.send_to_all_message_async(
                    self.user_name, user_message, 'user')
        else:
            self.user_name = command.get('user-name')
            if self.user_name == ".":
                self.close_async(True)
            else:
                await ChatRoom.send_to_all_message_async(
                    None, f'{self.user_name} Connected!', 'system')
                print(f'{self.user_name} with id {self.session_id} connected')

    async def close_async(self, from_server):
        if from_server:
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
        if (message.type == edge.MessageType.CONNECT):
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
    await ChatRoom.process_message_async(context.message, None, None)


@app.socket_action()
async def process_all_other_message_async(context: edge.SocketContext):
    print("process_all_other_message")
    await ChatRoom.process_message_async(context.message,
                                         context.cms, context.body)


#####
# Web
#####
@app.web_handler()
def process_web_message(_: edge.HttpContext):
    path = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "chat.html")
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


app.listening()
