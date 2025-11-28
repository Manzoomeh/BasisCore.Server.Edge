import asyncio
import base64
import json
import os
import pathlib
import ssl
import tempfile
from typing import TYPE_CHECKING, Awaitable, Callable, Optional

from cryptography.hazmat.primitives.serialization import (Encoding,
                                                          NoEncryption,
                                                          PrivateFormat,
                                                          pkcs12)

from bclib.listener.ilistener import IListener
from bclib.utility import DictEx, ResponseTypes
from bclib.utility.http_base_data_name import HttpBaseDataName
from bclib.utility.http_base_data_type import HttpBaseDataType

from ..endpoint import Endpoint
from ..message import Message
from .http_message import HttpMessage
from .web_request_helper import WebRequestHelper

if TYPE_CHECKING:
    from aiohttp import web
    from bclib.websocket import WebSocketSessionManager

from aiohttp.log import web_logger


class HttpListener(IListener):
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

    def __init__(self, endpoint: Endpoint, async_callback: 'Callable[[Message], Awaitable[Message]]', ssl_options: 'dict', configuration: Optional[DictEx], ws_manager: 'WebSocketSessionManager'):
        super().__init__(async_callback)
        self.__endpoint = endpoint
        self.ssl_options = ssl_options
        self.__config = configuration if configuration is not None else DictEx()
        self.__logger = self.__config.get(
            HttpListener.LOGGER, HttpListener._DEFAULT_LOGGER)
        self.__router = self.__config.get(
            HttpListener.ROUTER, HttpListener._DEFAULT_ROUTER)
        self.__middlewares = self.__config.get(
            HttpListener.MIDDLEWARES, HttpListener._DEFAULT_MIDDLEWARES)
        self.__handler_args = self.__config.get(
            HttpListener.HANDLER_ARGS, HttpListener._DEFAULT_HANDLER_ARGS)
        self.__client_max_size = self.__config.get(
            HttpListener.CLIENT_MAX_SIZE, HttpListener._DEFAULT_CLIENT_MAX_SIZE)
        self.__ws_manager = ws_manager

        # Use WebSocket session manager from dispatcher

    def initialize_task(self, event_loop: asyncio.AbstractEventLoop):
        event_loop.create_task(self.__server_task(event_loop))

    async def __server_task(self, event_loop: asyncio.AbstractEventLoop):
        from aiohttp import web

        async def on_request_receive_async(request: 'web.Request') -> web.Response:
            # Check for WebSocket upgrade
            if request.headers.get('Upgrade', '').lower() == 'websocket':
                return await self.__handle_websocket_async(request)

            # Handle regular HTTP request
            return await self.__handle_http_async(request)

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
        ssl_context = None
        if self.ssl_options:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            if "certfile" in self.ssl_options:
                ssl_context.load_cert_chain(
                    certfile=self.ssl_options.certfile,
                    keyfile=self.ssl_options.keyfile
                )
            elif "pfxfile" in self.ssl_options:
                fullchain_path, key_path = HttpListener.convert_pfx_to_temp_files(
                    self.ssl_options.pfxfile,
                    self.ssl_options.password
                )
                ssl_context.load_cert_chain(
                    certfile=fullchain_path, keyfile=key_path)

                # حذف فایل‌های موقت بعد از load
                os.remove(fullchain_path)
                os.remove(key_path)

        runner = web.AppRunner(app, handle_signals=True)
        await runner.setup()
        site = web.TCPSite(runner, self.__endpoint.url,
                           self.__endpoint.port, ssl_context=ssl_context)
        await site.start()
        print(
            f"Development Edge server started at http{'s' if self.ssl_options else ''}://{self.__endpoint.url}:{self.__endpoint.port}")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            print(
                f"Development Edge server for http{'s' if self.ssl_options else ''}://{self.__endpoint.url}:{self.__endpoint.port} stopped.")
            await site.stop()
            await runner.cleanup()
            await runner.shutdown()

    async def __handle_http_async(self, request: 'web.Request') -> 'web.Response':
        """
        Handle HTTP request

        Args:
            request: aiohttp web request

        Returns:
            web.Response object
        """
        from aiohttp import web
        from multidict import MultiDict

        ret_val: web.Response = None
        request_cms = await WebRequestHelper.create_cms_async(request)
        # Pass cms object directly without serialization overhead.
        msg = HttpMessage(request_cms, request)
        await self._on_message_receive(msg)

        # Check if handler used streaming response
        if msg.Response is not None:
            # Handler used streaming, return the StreamResponse directly
            return msg.Response

        # Use cms_object if HttpMessage, otherwise decode buffer
        cms_cms = msg.response_data[HttpBaseDataType.CMS]
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
                path = pathlib.Path(
                    cms_cms_webserver[HttpBaseDataName.FILE_PATH])
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
                ret_val.body = cms_cms[HttpBaseDataName.BLOB_CONTENT]
        return ret_val

    async def __handle_websocket_async(self, request: 'web.Request') -> 'web.Response':
        """
        Handle WebSocket connection

        Hand off to session manager which creates and returns WebSocket
        """
        # Create CMS object from request
        cms_object = await WebRequestHelper.create_cms_async(request)

        # Manager creates WebSocket, prepares it, and handles everything
        return await self.__ws_manager.handle_connection(request, cms_object)

    @staticmethod
    def convert_pfx_to_temp_files(pfxfile: str, password: str):
        """
        Convert a .pfx/.p12 file to temporary PEM files:
        - fullchain.pem (certificate + intermediates)
        - key.pem (private key)
        Returns: (fullchain_path, key_path)
        """
        with open(pfxfile, "rb") as f:
            private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                f.read(), password.encode()
            )

            # --- key.pem ---
            key_tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".key.pem")
            key_tmp.write(
                private_key.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=NoEncryption()
                )
            )
            key_tmp.flush()

            # --- fullchain.pem ---
            fullchain_tmp = tempfile.NamedTemporaryFile(
                delete=False, suffix=".fullchain.pem")
            # cert اصلی
            fullchain_tmp.write(certificate.public_bytes(Encoding.PEM))
            # chain cert ها
            if additional_certificates:
                for ca in additional_certificates:
                    fullchain_tmp.write(ca.public_bytes(Encoding.PEM))
            fullchain_tmp.flush()

            return fullchain_tmp.name, key_tmp.name
