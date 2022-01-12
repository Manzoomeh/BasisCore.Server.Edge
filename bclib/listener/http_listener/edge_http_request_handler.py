import cgi
import io
import datetime
import json
import uuid
from urllib.parse import unquote, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler

from ..http_listener.http_base_data_type import HttpBaseDataType
from ..http_listener.http_base_data_name import HttpBaseDataName

from ..message_type import MessageType
from ..message import Message


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
        headercode: str = cms[HttpBaseDataType.CMS][HttpBaseDataType.WEB_SERVER]["headercode"]
        self.send_response(int(headercode.split(' ')[0]))
        self.send_header(
            "Content-type", cms[HttpBaseDataType.CMS][HttpBaseDataType.WEB_SERVER]["mime"])
        if HttpBaseDataName.HTTP in cms[HttpBaseDataType.CMS]:
            http: dict = cms[HttpBaseDataType.CMS][HttpBaseDataName.HTTP]
            if http:
                for key, value in http.items():
                    self.send_header(key, ",".join(
                        value) if isinstance(value, list)else value)
        self.end_headers()
        self.wfile.write(
            bytes(cms[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT], "utf-8"))

    def __create_cms_object_from_requester(self) -> dict:
        cms_object = dict()
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.METHODE, self.command.lower())
        raw_url = unquote(self.path)[1:]
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.RAW_URL, raw_url)
        url_object = urlparse(raw_url)
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.URL, url_object.path)
        self.__add_query_string(url_object.query, cms_object)
        for key, value in self.headers.items():
            field_name = key.strip().lower()
            if field_name == HttpBaseDataName.COOKIE:
                self.__add_cookie(value, cms_object)
            elif field_name == HttpBaseDataName.HOST:
                self.__add_host(value, raw_url, cms_object)
            else:
                self.__add_header(cms_object, HttpBaseDataType.REQUEST,
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
            self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                              HttpBaseDataName.BODY, body)
            content_type: str = self.headers.get("content-type")
            if content_type and content_type != "application/json":
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
                                          HttpBaseDataType.FORM, key, value[0] if len(value) == 1 else value)
                else:
                    for key, value in parse_qs(body).items():
                        self.__add_header(
                            cms_object, HttpBaseDataType.FORM, key, value[0] if len(value) == 1 else value)

    def __add_server_data(self, cms_object: dict):
        EdgeHTTPRequestHandler._id += 1
        now = datetime.datetime.now()
        self.__add_header(cms_object, HttpBaseDataType.CMS,
                          HttpBaseDataName.DATE, now.strftime("%d/%m/%Y"))
        self.__add_header(cms_object, HttpBaseDataType.CMS,
                          HttpBaseDataName.TIME, now.strftime("%H:%M"))
        self.__add_header(cms_object, HttpBaseDataType.CMS,
                          HttpBaseDataName.DATE2, now.strftime("%Y%m%d"))
        self.__add_header(cms_object, HttpBaseDataType.CMS,
                          HttpBaseDataName.TIME2, now.strftime("%H%M%S"))
        self.__add_header(cms_object, HttpBaseDataType.CMS,
                          HttpBaseDataName.DATE3, now.strftime("%Y.%m.%d"))
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.REQUEST_ID, str(EdgeHTTPRequestHandler._id))
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.HOST_IP, self.server.server_address[0])
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.HOST_PORT, str(self.server.server_address[1]))
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.CLIENT_IP, str(self.client_address[0]))

    def __add_query_string(self, value: str, cms_object: dict) -> None:
        query = parse_qs(value)
        for key, value in query.items():
            for item in value:
                self.__add_header(
                    cms_object, HttpBaseDataType.QUERY, key, item)

    def __add_cookie(self, raw_header_value: str, cms_object) -> None:
        for item in raw_header_value.split(';'):
            parts = item.split('=')
            if len(parts) == 2:
                self.__add_header(cms_object, HttpBaseDataName.COOKIE,
                                  parts[0].strip(), parts[1].strip())

    def __add_host(self, row_host: str, row_url: str, cms_object) -> None:
        host_parts = row_host.split(':')
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.HOST, host_parts[0])
        if len(host_parts) == 2:
            self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                              HttpBaseDataName.PORT, host_parts[1])
        self.__add_header(cms_object, HttpBaseDataType.REQUEST,
                          HttpBaseDataName.FULL_URL,  f"{row_host}/{row_url}")

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
