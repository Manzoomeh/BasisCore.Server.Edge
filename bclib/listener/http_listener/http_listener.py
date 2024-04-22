import asyncio
import cgi
import io
import datetime
import json
import uuid
import base64
from typing import Callable, Coroutine, TYPE_CHECKING, Optional

from urllib.parse import unquote, parse_qs
from ..endpoint import Endpoint
from ..http_listener.http_base_data_name import HttpBaseDataName
from ..http_listener.http_base_data_type import HttpBaseDataType
from bclib.utility import DictEx
from ..message_type import MessageType
from ..message import Message

if TYPE_CHECKING:
    from aiohttp import web

from aiohttp.log import web_logger

class HttpListener:
    _id = 0
    LOGGER = "logger"
    ROUTER = "router"
    MIDDLEWARES = "middlewares"
    HANDLER_ARGS = "handler_args"
    CLIENT_MAX_SIZE = "client_max_size"

    _DEFAULT_LOGGER = web_logger
    _DEFAULT_ROUTER = None
    _DEFAULT_MIDDLEWARES = ()
    _DEFAULT_HANDLER_ARGS = None
    _DEFAULT_CLIENT_MAX_SIZE = 1024 ** 2
    

    def __init__(self, endpoint: Endpoint, async_callback: 'Callable[[Message], Coroutine[Message]]', configuration: Optional[DictEx]):
        self.__endpoint = endpoint
        self.on_message_receive_async = async_callback
        self.__config = configuration if configuration is not None else DictEx()
        self.__logger = self.__config.get(HttpListener.LOGGER, HttpListener._DEFAULT_LOGGER)
        self.__router = self.__config.get(HttpListener.ROUTER, HttpListener._DEFAULT_ROUTER)
        self.__middlewares = self.__config.get(HttpListener.MIDDLEWARES, HttpListener._DEFAULT_MIDDLEWARES)
        self.__handler_args = self.__config.get(HttpListener.HANDLER_ARGS, HttpListener._DEFAULT_HANDLER_ARGS)
        self.__client_max_size = self.__config.get(HttpListener.CLIENT_MAX_SIZE, HttpListener._DEFAULT_CLIENT_MAX_SIZE)
        

    def initialize_task(self, event_loop: asyncio.AbstractEventLoop):
        event_loop.create_task(self.__server_task(event_loop))

    async def __server_task(self, event_loop: asyncio.AbstractEventLoop):
        from aiohttp import web
        from multidict import MultiDict

        async def on_request_receive_async(request: 'web.Request') -> web.Response:
            ret_val: web.Response = None
            cms_object = await self.create_cms_async(request)
            msg = Message(str(uuid.uuid4()), MessageType.AD_HOC,
                          json.dumps(cms_object).encode())
            result = await self.on_message_receive_async(msg)
            if result:
                cms: dict = json.loads(result.buffer.decode("utf-8"))
                header_code: str = cms[HttpBaseDataType.CMS][HttpBaseDataType.WEB_SERVER]["headercode"]
                mime = cms[HttpBaseDataType.CMS][HttpBaseDataName.WEB_SERVER]["mime"]
                headers: MultiDict = None
                if HttpBaseDataName.HTTP in cms[HttpBaseDataType.CMS]:
                    http: dict = cms[HttpBaseDataType.CMS][HttpBaseDataName.HTTP]
                    if http:
                        headers = MultiDict()
                        for key, value in http.items():
                            if isinstance(value, list):
                                for item in value:
                                    headers.add(key, item)
                            else:
                                headers.add(key, value)
                ret_val = web.Response(
                    status=int(header_code.split(' ')[0]),
                    headers=headers,
                    content_type=mime)
                if HttpBaseDataName.CONTENT in cms[HttpBaseDataType.CMS]:
                    ret_val.text = cms[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT]
                else:
                    raw_blob_content = cms[HttpBaseDataType.CMS][HttpBaseDataName.BLOB_CONTENT]
                    ret_val.body = base64.b64decode(raw_blob_content.encode("utf-8"))
            else:
                ret_val = web.Response()
            return ret_val

        app = web.Application(
            logger=self.__logger,
            router=self.__router,
            middlewares=self.__middlewares,
            handler_args=self.__handler_args,
            client_max_size=self.__client_max_size,
            loop=event_loop
        )
        app.add_routes(
            [web.route('*', '/{tail:.*}', on_request_receive_async)])
        runner = web.AppRunner(app, handle_signals=True)
        await runner.setup()
        site = web.TCPSite(runner, self.__endpoint.url, self.__endpoint.port)
        await site.start()
        print(
            f"Development Edge server started at http://{self.__endpoint.url}:{self.__endpoint.port}")
        try:
            while True:
                await asyncio.sleep(.0001)
        except asyncio.CancelledError:
            pass
        finally:
            print("Development Edge server stopped.")
            await site.stop()
            await runner.cleanup()
            await runner.shutdown()

    @staticmethod
    async def create_cms_async(request: 'web.Request') -> dict:
        cms_object = dict()
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.METHODE, request.method.lower())
        raw_url = unquote(request.path_qs)[1:]
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.RAW_URL, raw_url)
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.URL, request.path[1:])
        HttpListener.__add_query_string(request.query, cms_object)
        for key, value in request.headers.items():
            field_name = key.strip().lower()
            if field_name == HttpBaseDataName.COOKIE:
                HttpListener.__add_cookie(value, cms_object)
            elif field_name == HttpBaseDataName.HOST:
                HttpListener.__add_host(value, raw_url, cms_object)
            else:
                HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                          field_name, str(value).strip())
        HttpListener.__add_server_data(cms_object, request)
        await HttpListener.__add_body_async(cms_object, request)
        return {"cms": cms_object}

    @staticmethod
    async def __add_body_async(cms_object: dict, request: 'web.Request'):
        content_len_str = request.headers.get('Content-Length')
        if content_len_str or request.can_read_body:
            raw_body = await request.read()
            body = raw_body.decode('utf-8')
            HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.BODY, body)
            content_type: str = request.headers.get(
                "content-type")
            if content_type and content_type.find("application/json") < 0:
                if content_type.find("multipart/form-data") >= 0:
                    _, content_type_value_params = cgi.parse_header(
                        content_type)
                    content_type_value_params['boundary'] = bytes(
                        content_type_value_params['boundary'], "utf-8")
                    if content_len_str is not None:
                        content_type_value_params['CONTENT-LENGTH'] = int(
                            content_len_str)
                    with io.BytesIO(raw_body) as stream:
                        fields = cgi.parse_multipart(
                            stream, content_type_value_params)
                    for key, value in fields.items():
                        HttpListener.__add_header(cms_object,
                                                  HttpBaseDataType.FORM, key, value[0] if len(value) == 1 else value)
                else:
                    for key, value in parse_qs(body).items():
                        HttpListener.__add_header(
                            cms_object, HttpBaseDataType.FORM, key, value[0] if len(value) == 1 else value)

    @staticmethod
    def __add_server_data(cms_object: dict, request: 'web.Request'):
        HttpListener._id += 1
        now = datetime.datetime.now()
        HttpListener.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.DATE, now.strftime("%d/%m/%Y"))
        HttpListener.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.TIME, now.strftime("%H:%M"))
        HttpListener.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.DATE2, now.strftime("%Y%m%d"))
        HttpListener.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.TIME2, now.strftime("%H%M%S"))
        HttpListener.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.DATE3, now.strftime("%Y.%m.%d"))
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.REQUEST_ID, str(HttpListener._id))
        host_parts = request.host.split(':')
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.HOST_IP, host_parts[0])
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.HOST_PORT,  host_parts[1] if len(host_parts) > 1 else "80")  # edit
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.CLIENT_IP, str(request.remote))

    @staticmethod
    def __add_query_string(query: dict, cms_object: dict) -> None:
        for key, value in query.items():
            HttpListener.__add_header(
                cms_object, HttpBaseDataType.QUERY, key, value)

    @staticmethod
    def __add_cookie(raw_header_value: str, cms_object) -> None:
        for item in raw_header_value.split(';'):
            parts = item.split('=')
            if len(parts) == 2:
                HttpListener.__add_header(cms_object, HttpBaseDataName.COOKIE,
                                          parts[0].strip(), parts[1].strip())

    @staticmethod
    def __add_host(row_host: str, row_url: str, cms_object) -> None:
        host_parts = row_host.split(':')
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.HOST, host_parts[0])
        if len(host_parts) == 2:
            HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.PORT, host_parts[1])
        HttpListener.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.FULL_URL,  f"{row_host}/{row_url}")

    @staticmethod
    def __add_header(cms_object: dict, value_type: str, value_name: str, value: str) -> None:
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
