import json
from pywebpush import webpush


class WebPush():
    def __init__(self, options: 'dict') -> None:
        self.__dic = dict()
        if "push" not in options:
            raise Exception("push setting not found in host settings")
        if 'vapid' not in options["push"]:
            raise Exception("push.vapid setting not found in host settings")
        if 'subject' not in options["push"]["vapid"]:
            raise Exception(
                "push.vapid.subject setting not found in host settings")
        if 'private_key' not in options["push"]["vapid"]:
            raise Exception(
                "push.vapid.private_key setting not found in host settings")
        if 'public_key' not in options["push"]["vapid"]:
            raise Exception(
                "push.vapid.public_key setting not found in host settings")

        self.__vapid_private_key = options["push"]["vapid"]["private_key"]
        self.__vapid_public_key = options["push"]["vapid"]["public_key"]
        self.__vapid_subject = options["push"]["vapid"]["subject"]

    def add_subscriber(self, client: str, endpoint: str, p256dh: str, auth: str) -> None:
        self.__dic[client] = {
            "endpoint": endpoint,
            "keys": {
                "p256dh": p256dh,
                "auth": auth
            }
        }

    def push_object(self, client: str, message_type: str, obj: dict, offline_message: str = None, url: str = None) -> bool:
        data = {
            "sources": [
                {
                    "data": [obj]
                }
            ]
        }
        return self.push(client, message_type, data, offline_message, url)

    def push(self, client: str, message_type: str, message: dict, offline_message: str = None, url: str = None) -> bool:
        msg = {
            "type": message_type,
            "message": message
        }
        if offline_message:
            msg["offlineMessage"] = offline_message
        if url:
            msg["url"] = url
        ret_val = True
        data = json.dumps(msg)
        if client in self.__dic:
            subscription_info = self.__dic[client]
            webpush(subscription_info, data, self.__vapid_private_key,
                    vapid_claims={"sub": self.__vapid_subject})
        else:
            ret_val = False
        return ret_val
