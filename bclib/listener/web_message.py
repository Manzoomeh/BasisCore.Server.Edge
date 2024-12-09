import base64
import pathlib
import cgi
import io
import datetime
from aiohttp import web
from urllib.parse import unquote, parse_qs
from typing import Any, Coroutine, Optional, Union
from multidict import MultiDict
from aiohttp.web_response import ContentCoding
from bclib.utility.response_types import ResponseTypes
from bclib.listener.http_listener.http_base_data_name import HttpBaseDataName
from bclib.listener.http_listener.http_base_data_type import HttpBaseDataType
from bclib.listener.message import Message

class WebMessage(Message):
    _id = 0
    def __init__(self,  request: 'web.Request') -> None:
        super().__init__()
        self.__request = request
        self.Response: web.Response = None

    async def get_json_async(self) -> Coroutine[Any, Any, dict]:
        return await self.create_cms_async(self.__request)

    async def set_result_async(self,cms:dict):
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
                self.Response = web.FileResponse(
                    path=path,
                    chunk_size=256*1024,
                    status=int(header_code.split(' ')[0]),
                    headers=headers
                )
            except FileNotFoundError:
                self.Response = web.Response(
                    status=404,
                    reason="File not found"
                )
        else:
            self.Response = web.Response(
                status=int(header_code.split(' ')[0]),
                headers=headers
            )
            if HttpBaseDataName.CONTENT in cms_cms:
                value = cms_cms[HttpBaseDataName.CONTENT]
                self.Response.text =value if value is None or isinstance(value,str) else str(value)
            else:
                raw_blob_content = cms_cms[HttpBaseDataName.BLOB_CONTENT]
                #TODO:Check for remove extra encoding
                self.Response.body = base64.b64decode(raw_blob_content.encode("utf-8"))

    @staticmethod
    async def create_cms_async(request: 'web.Request') -> dict:
        cms_object = dict()
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.METHODE, request.method.lower())
        raw_url = unquote(request.path_qs)[1:]
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.RAW_URL, raw_url)
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.URL, request.path[1:])
        WebMessage.__add_query_string(request.query, cms_object)
        for key, value in request.headers.items():
            field_name = key.strip().lower()
            if field_name == HttpBaseDataName.COOKIE:
                WebMessage.__add_cookie(value, cms_object)
            elif field_name == HttpBaseDataName.HOST:
                WebMessage.__add_host(value, raw_url, cms_object)
            else:
                WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                          field_name, str(value).strip())
        WebMessage.__add_server_data(cms_object, request)
        await WebMessage.__add_body_async(cms_object, request)
        return {"cms": cms_object}

    @staticmethod
    async def __add_body_async(cms_object: dict, request: 'web.Request'):
        content_len_str = request.headers.get('Content-Length')
        if content_len_str or request.can_read_body:
            raw_body = await request.read()
            body = raw_body.decode('utf-8')
            WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
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
                        WebMessage.__add_header(cms_object,
                                                  HttpBaseDataType.FORM, key, value[0] if len(value) == 1 else value)
                else:
                    for key, value in parse_qs(body).items():
                        WebMessage.__add_header(
                            cms_object, HttpBaseDataType.FORM, key, value[0] if len(value) == 1 else value)

    @staticmethod
    def __add_server_data(cms_object: dict, request: 'web.Request'):
        WebMessage._id += 1
        now = datetime.datetime.now()
        WebMessage.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.DATE, now.strftime("%d/%m/%Y"))
        WebMessage.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.TIME, now.strftime("%H:%M"))
        WebMessage.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.DATE2, now.strftime("%Y%m%d"))
        WebMessage.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.TIME2, now.strftime("%H%M%S"))
        WebMessage.__add_header(cms_object, HttpBaseDataType.CMS,
                                  HttpBaseDataName.DATE3, now.strftime("%Y.%m.%d"))
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.REQUEST_ID, str(WebMessage._id))
        host_parts = request.host.split(':')
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.HOST_IP, host_parts[0])
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.HOST_PORT,  host_parts[1] if len(host_parts) > 1 else "80")  # edit
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.CLIENT_IP, str(request.remote))

    @staticmethod
    def __add_query_string(query: dict, cms_object: dict) -> None:
        for key, value in query.items():
            WebMessage.__add_header(
                cms_object, HttpBaseDataType.QUERY, key, value)

    @staticmethod
    def __add_cookie(raw_header_value: str, cms_object) -> None:
        for item in raw_header_value.split(';'):
            parts = item.split('=')
            if len(parts) == 2:
                WebMessage.__add_header(cms_object, HttpBaseDataName.COOKIE,
                                          parts[0].strip(), parts[1].strip())

    @staticmethod
    def __add_host(row_host: str, row_url: str, cms_object) -> None:
        host_parts = row_host.split(':')
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                  HttpBaseDataName.HOST, host_parts[0])
        if len(host_parts) == 2:
            WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.PORT, host_parts[1])
        WebMessage.__add_header(cms_object, HttpBaseDataType.REQUEST,
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

    async def start_stream_response_async(self,status: int = 200,
        reason: Optional[str] = 'OK',
        headers: Optional[dict] = None,):
        if self.Response is not None:
            raise Exception('StreamResponse started')
        self.Response = web.StreamResponse(status=status, 
                                    reason=reason, 
                                    headers=headers)
        await self.Response.prepare(self.__request)

    async def write_async(self,data:'bytes') -> Coroutine[Any, Any, None]:
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.write(data)

    async def  drain_async(self) -> Coroutine[Any, Any, None]:
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.drain()

    async def  enable_compression(self,force: Optional[Union[bool, ContentCoding]] = None) -> None:
        if self.Response is None:
            raise Exception('StreamResponse not started')
        await self.Response.enable_compression(force)