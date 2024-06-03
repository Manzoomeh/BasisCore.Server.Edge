import asyncio
import cgi
import io
import datetime
import json
import uuid
import ssl
from typing import Callable, Coroutine, TYPE_CHECKING
from cryptography.hazmat.primitives.serialization import pkcs12,Encoding,PrivateFormat,NoEncryption

from urllib.parse import unquote, parse_qs
from ..endpoint import Endpoint
from ..http_listener.http_base_data_name import HttpBaseDataName
from ..http_listener.http_base_data_type import HttpBaseDataType

from ..message_type import MessageType
from ..message import Message

if TYPE_CHECKING:
    from aiohttp import web


class HttpListener:
    _id = 0

    def __init__(self, endpoint: Endpoint, async_callback: 'Callable[[Message], Coroutine[Message]]',ssl_options:'dict'):
        self.__endpoint = endpoint
        self.on_message_receive_async = async_callback
        self.ssl_options = ssl_options

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
                    content_type=mime,
                    text=cms[HttpBaseDataType.CMS][HttpBaseDataName.CONTENT])
            else:
                ret_val = web.Response()
            return ret_val

        app = web.Application(loop=event_loop)
        app.add_routes(
            [web.route('*', '/{tail:.*}', on_request_receive_async)])
        ssl_context= None
        if self.ssl_options :
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            if('certfile' in self.ssl_options):
                ssl_context.load_cert_chain(certfile=self.ssl_options.certfile,keyfile=self.ssl_options.keyfile)
            elif('pfxfile' in self.ssl_options):
                try:
                    pem_file_path = HttpListener.convert_pfx_to_pem_file(self.ssl_options.pfxfile,self.ssl_options.password)
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
                await asyncio.sleep(.0001)
        except asyncio.CancelledError:
            pass
        finally:
            print("Development Edge server stopped.")
            await site.stop()
            await runner.cleanup()
            await runner.shutdown()

    @staticmethod
    def convert_pfx_to_pem_file(pfxfile:str,password:str)->str:
        with open(pfxfile,"rb") as f:
            try:
                private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(f.read(), password.encode())
                pem_file_path = '{0}.auto-generated.pem'.format(pfxfile)
                with open(pem_file_path, 'wb') as key_file:
                    key_file.write(certificate.public_bytes(Encoding.PEM))
                    for item in additional_certificates:
                        key_file.write(item.public_bytes(Encoding.PEM))
                    key_file.write(private_key.private_bytes(encoding= Encoding.PEM,format=PrivateFormat.TraditionalOpenSSL,encryption_algorithm=NoEncryption()))
                return pem_file_path
            except Exception as ex:
                raise Exception("Error in create pen file from pfx {0}: {1}".format(self.ssl_options.pfxPath, ex))

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
