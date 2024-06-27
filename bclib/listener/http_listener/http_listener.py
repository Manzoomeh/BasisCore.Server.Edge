import asyncio
import cgi
import io
import datetime
import json
import uuid
import ssl
import base64
from typing import Callable, TYPE_CHECKING, Optional, Awaitable
from urllib.parse import unquote, parse_qs
from ..endpoint import Endpoint
from ..http_listener.http_base_data_name import HttpBaseDataName
from ..http_listener.http_base_data_type import HttpBaseDataType
from bclib.utility import DictEx, ResponseTypes
from ..message import Message
import pathlib

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
    

    def __init__(self, endpoint: Endpoint, async_callback: 'Callable[[Message], Awaitable[Message]]',ssl_options:'dict', configuration: Optional[DictEx]):
        self.__endpoint = endpoint
        self.on_message_receive_async = async_callback
        self.ssl_options = ssl_options
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
            request_cms = await self.create_cms_async(request)
            msg = Message.create_add_hock(
                str(uuid.uuid4()),
                json.dumps(request_cms, ensure_ascii=False).encode(encoding="utf-8")
            )
            result = await self.on_message_receive_async(msg)
            if result:
                cms: dict = json.loads(result.buffer.decode("utf-8"))
                cms_cms = cms[HttpBaseDataType.CMS]
                cms_cms_webserver = cms_cms[HttpBaseDataType.WEB_SERVER]
                index = cms_cms_webserver[HttpBaseDataName.INDEX]
                header_code: str = cms_cms_webserver[HttpBaseDataName.HEADER_CODE]
                mime = cms_cms[HttpBaseDataName.WEB_SERVER][HttpBaseDataName.MIME]
                headers = MultiDict()
                if HttpBaseDataName.HTTP in cms_cms:
                    http: dict = cms_cms[HttpBaseDataName.HTTP]
                    for key, value in http.items():
                        if isinstance(value, list):
                            for item in value:
                                headers.add(key, item)
                        else:
                            headers.add(key, value)
                headers.add("Content-Type", mime)
                if index == ResponseTypes.STATIC_FILE:
                    try:
                        path = pathlib.Path(cms_cms_webserver[HttpBaseDataName.FILE_PATH])
                        path.stat()
                        ret_val = web.FileResponse(
                            path=path,
                            chunk_size=256*1024,
                            status=int(header_code.split(' ')[0]),
                            headers=headers
                        )
                    except FileNotFoundError:
                        ret_val = web.Response(
                            status=404,
                            reason="File not found"
                        )
                else:
                    ret_val = web.Response(
                        status=int(header_code.split(' ')[0]),
                        headers=headers
                    )
                    if HttpBaseDataName.CONTENT in cms_cms:
                        ret_val.text = cms_cms[HttpBaseDataName.CONTENT]
                    else:
                        raw_blob_content = cms_cms[HttpBaseDataName.BLOB_CONTENT]
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
        ssl_context= None
        if self.ssl_options:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            if 'certfile' in self.ssl_options:
                ssl_context.load_cert_chain(
                    certfile=self.ssl_options.certfile,
                    keyfile=self.ssl_options.keyfile
                )
            elif 'pfxfile' in self.ssl_options:
                try:
                    pem_file_path = HttpListener.convert_pfx_to_pem_file(
                        self.ssl_options.pfxfile,
                        self.ssl_options.password
                    )
                    ssl_context.load_cert_chain(certfile=pem_file_path)
                except Exception as e:
                    raise Exception("Invalid PKCS12 or pastphrase for {0}: {1}".format(self.ssl_options.pfxfile, e))

        runner = web.AppRunner(app, handle_signals=True)
        await runner.setup()
        site = web.TCPSite(runner, self.__endpoint.url, self.__endpoint.port, ssl_context=ssl_context)
        await site.start()
        print(
            f"Development Edge server started at http{'s' if self.ssl_options else ''}://{self.__endpoint.url}:{self.__endpoint.port}")
        try:
            while True:
                await asyncio.Future()
        except asyncio.CancelledError:
            pass
        finally:
            print("Development Edge server stopped.")
            await site.stop()
            await runner.cleanup()
            await runner.shutdown()

    @staticmethod
    def convert_pfx_to_pem_file(pfxfile:str,password:str)->str:
        from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
        with open(pfxfile,"rb") as f:
            try:
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(f.read(), password.encode())
                pem_file_path = '{0}.auto-generated.pem'.format(pfxfile)
                with open(pem_file_path, 'wb') as pem_file:
                    pem_file.write(certificate.public_bytes(Encoding.PEM))
                    for item in additional_certificates:
                        pem_file.write(item.public_bytes(Encoding.PEM))
                    pem_file.write(private_key.private_bytes(encoding= Encoding.PEM,format=PrivateFormat.TraditionalOpenSSL,encryption_algorithm=NoEncryption()))
                return pem_file_path
            except Exception as ex:
                raise Exception("Error in create pem file from pfx {0}: {1}".format(pfxfile, ex))

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
