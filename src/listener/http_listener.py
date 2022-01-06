import cgi
import io
import asyncio
import datetime
import json
from typing import Callable

from .message_type import MessageType
from .message import Message
from .endpoint import EndPoint
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlparse, parse_qs
import uuid


class HttpBaseDataType:
    WebServer = "webserver"
    Cms = "cms"
    Request = "request"
    Cookie = "cookie"
    Form = "form"
    Query = "query"
    Json = "json"
    Header = "header"
    Http = "http"
    Index4 = "index4"


class HttpBaseDataName:
    Methode = "methode"
    RawUrl = "rawurl"
    Debug = "debug"
    Host = "host"
    Cookie = "cookie"
    content_type = "content-type"
    FullUrl = "full-url"
    Port = "port"
    Url = "url"
    RequestId = "request-id"
    HostIP = "hostip"
    HostPort = "hostport"
    ClientIP = "clientip"
    Date = "date"
    Date2 = "date2"
    Date3 = "date3"
    Time = "time"
    Time2 = "time2"
    Body = "body"


class EdgeHTTPRequestHandler(BaseHTTPRequestHandler):
    _id = 0

    def do_GET(self):
        self.__process_request()

    def do_POST(self):
        self.__process_request()

    def do_PUT(self):
        self.__process_request()

    def do_DELETE(self):
        self.__process_request()

    def do_PATCH(self):
        self.__process_request()

    def do_HEAD(self):
        self.__process_request()

    def do_OPTIONS(self):
        self.__process_request()

    def __process_request(self):
        cms_object = self.__create_cms_object_from_requester()
        msg = Message(str(uuid.uuid4()), MessageType.AD_HOC,
                      json.dumps(cms_object).encode())
        result: Message = self.server.on_message_receive(msg)

        cms: dict = json.loads(result.buffer.decode("utf-8"))
        headercode: str = cms["cms"]["webserver"]["headercode"]
        self.send_response(int(headercode.split(' ')[0]))
        self.send_header("Content-type", cms["cms"]["webserver"]["mime"])
        self.end_headers()
        self.wfile.write(bytes(cms["cms"]["content"], "utf-8"))

    def __create_cms_object_from_requester(self) -> dict:
        cms_object = dict()
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.Methode, self.command.lower())
        raw_url = unquote(self.path)[1:]
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.RawUrl, raw_url)
        url_object = urlparse(raw_url)
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.Url, url_object.path)
        self.__add_query_string(url_object.query, cms_object)
        for key, value in self.headers.items():
            field_name = key.strip().lower()
            if field_name == HttpBaseDataName.Cookie:
                self.__add_cookie(value, cms_object)
            elif field_name == HttpBaseDataName.Host:
                self.__add_host(value, raw_url, cms_object)
            else:
                self.__add_header(cms_object, HttpBaseDataType.Request,
                                  field_name, str(value).strip())
        self.__add_server_data(cms_object)
        self.__add_body(cms_object)
        return {"cms": cms_object}

    def __add_body(self, cms_object: dict):
        content_len_str = self.headers.get('Content-Length')
        if content_len_str:
            content_len = int(content_len_str)
            raw_body = self.rfile.read(content_len)
            body = raw_body.decode('utf-8')
            self.__add_header(cms_object, HttpBaseDataType.Request,
                              HttpBaseDataName.Body, body)
            content_type: str = self.headers.get("content-type")
            if content_type != "application/json":
                if content_type.find("multipart/form-data") > -1:
                    _, content_type_value_params = cgi.parse_header(
                        content_type)
                    content_type_value_params['boundary'] = bytes(
                        content_type_value_params['boundary'], "utf-8")
                    content_type_value_params['CONTENT-LENGTH'] = content_len
                    with io.BytesIO(raw_body) as stream:
                        fields = cgi.parse_multipart(
                            stream, content_type_value_params)
                    for key, value in fields.items():
                        self.__add_header(cms_object,
                                          HttpBaseDataType.Form, key, value[0] if len(value) == 1 else value)
                else:
                    for key, value in parse_qs(body).items():
                        self.__add_header(
                            cms_object, HttpBaseDataType.Form, key, value[0] if len(value) == 1 else value)

    def __add_server_data(self, cms_object: dict):
        EdgeHTTPRequestHandler._id += 1
        now = datetime.datetime.now()
        self.__add_header(cms_object, HttpBaseDataType.Cms,
                          HttpBaseDataName.Date, now.strftime("%d/%m/%Y"))
        self.__add_header(cms_object, HttpBaseDataType.Cms,
                          HttpBaseDataName.Time, now.strftime("%H:%M"))
        self.__add_header(cms_object, HttpBaseDataType.Cms,
                          HttpBaseDataName.Date2, now.strftime("%Y%m%d"))
        self.__add_header(cms_object, HttpBaseDataType.Cms,
                          HttpBaseDataName.Time2, now.strftime("%H%M%S"))
        self.__add_header(cms_object, HttpBaseDataType.Cms,
                          HttpBaseDataName.Date3, now.strftime("%Y.%m.%d"))
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.RequestId, str(EdgeHTTPRequestHandler._id))
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.HostIP, self.server.server_address[0])
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.HostPort, str(self.server.server_address[1]))
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.ClientIP, str(self.client_address[1]))

    def __add_query_string(self, value: str, cms_object: dict) -> None:
        query = parse_qs(value)
        for key, value in query.items():
            for item in value:
                self.__add_header(
                    cms_object, HttpBaseDataType.Query, key, item)

    def __add_cookie(self, raw_header_value: str, cms_object) -> None:
        for item in raw_header_value.split(';'):
            parts = item.split('=')
            if len(parts) == 2:
                self.__add_header(cms_object, HttpBaseDataName.Cookie,
                                  parts[0].strip(), parts[1].strip())

    def __add_host(self, row_host: str, row_url: str, cms_object) -> None:
        host_parts = row_host.split(':')
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.Host, host_parts[0])
        if len(host_parts) == 2:
            self.__add_header(cms_object, HttpBaseDataType.Request,
                              HttpBaseDataName.Port, host_parts[1])
        self.__add_header(cms_object, HttpBaseDataType.Request,
                          HttpBaseDataName.FullUrl,  f"{row_host}/{row_url}")

    def __add_header(self, cms_object: dict, value_type: str, value_name: str, value: str) -> None:
        if value_type not in cms_object:
            cms_object[value_type] = dict()
        type_node = cms_object[value_type]
        if value_name in type_node:
            name_node = type_node[value_name]
            if isinstance(name_node, list):
                name_node.append(value)
            else:
                type_node[value_name] = [name_node, value]
        else:
            type_node[value_name] = value


class HttpListener:
    def __init__(self, endpoint: EndPoint, callBack: Callable[[Message], Message]):
        self.__endpoint = endpoint
        self.on_message_receive = callBack

    async def process_async(self):
        webServer = HTTPServer(
            (self.__endpoint.url,  self.__endpoint.port), EdgeHTTPRequestHandler)
        webServer.on_message_receive = self.on_message_receive
        print(
            f"Development Edge server started at http://{self.__endpoint.url}:{self.__endpoint.port}")

        try:
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass

        webServer.server_close()
        print("Development Edge server stopped.")

        while True:
            loop = asyncio.get_event_loop()
            receiver_task = loop.run_in_executor(
                None, self.__start_receiver, loop)
            sender_task = loop.run_in_executor(
                None, self.__start_sender, loop)
            await asyncio.gather(receiver_task, sender_task, return_exceptions=True)
