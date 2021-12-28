import json
import datetime
import xml.etree.ElementTree
import context
import dispatcher
from listener import Message
from listener.message_type import MessageType
from utility.DictEx import DictEx


options = {
    "sender": {
        "ip": "127.0.0.1",
        "port": 1025,
    },
    "receiver": {
        "ip": "127.0.0.1",
        "port": 1026,
    },
    "router": {
        "web": ["*"]
    }
}


app = dispatcher.DuplexSocketDispatcher(options)


class Client:

    def __init__(self, sessionId: str, cms: DictEx):
        self.cms = cms
        self.SessionId = sessionId
        self.UserName = None

    def update(self, message: str):
        data = json.loads(message)
        command = xml.etree.ElementTree.fromstring(data["command"])
        if self.UserName == None:
            self.UserName = command.get('user-name')
            if(self.UserName == "."):
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
            app.send_message(Message.create_disconnect(self.SessionId))

        ChatRoom.send_to_all_message(
            None, f"{self.UserName} Disconnected!", 'system')
        print(f'{self.UserName} Disconnected')


class ChatRoom:

    __sessions: dict[str, Client] = {}

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
            app.send_message(Message.create_from_text(session_id, msg))

    @staticmethod
    def process_message(message: Message, cms: DictEx):
        if(message.type == MessageType.connect):
            ChatRoom.__sessions[message.session_id] = Client(
                message.session_id, cms)
        elif message.type == MessageType.disconnect:
            if message.session_id in ChatRoom.__sessions:
                ChatRoom.__sessions[message.session_id].close(False)
                del ChatRoom.__sessions[message.session_id]
        elif message.type == MessageType.message:
            if message.session_id in ChatRoom.__sessions:
                ChatRoom.__sessions[message.session_id].update(cms.body)
        elif message.type == MessageType.ad_hoc:
            if message.session_id in ChatRoom.__sessions:
                print("adhoc message receive!")


@ app.web_action()
def process_rabbit_message2(context: context.WebContext):
    print("process_rabbit_message2")
    ChatRoom.process_message(context.message, context.cms)


app.listening()
