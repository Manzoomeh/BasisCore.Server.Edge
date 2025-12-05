"""HTTP Listener Implementation for BasisCore Edge

Provides HTTP/HTTPS server functionality with WebSocket support, SSL/TLS configuration,
and CMS-based request/response handling.

Features:
    - HTTP/HTTPS server with configurable SSL/TLS (cert files or PFX)
    - WebSocket connection handling via session manager
    - CMS-based request parsing and response generation
    - Static file serving with chunked transfer
    - Configurable middleware and routing
    - Streaming response support

Example:
    ```python
    from bclib.listener.http import HttpListener
    from bclib.listener import Endpoint
    
    # Create HTTP listener
    listener = HttpListener(
        endpoint=Endpoint("localhost:8080"),
        async_callback=dispatcher.on_message_receive_async,
        ssl_options=None,
        configuration=None,
        ws_manager=ws_manager
    )
    
    # Initialize and start
    listener.initialize_task(event_loop)
    ```
"""
import asyncio
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
from bclib.logger.ilogger import ILogger
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
    """HTTP/HTTPS server listener with WebSocket support

    Handles HTTP requests and WebSocket connections using aiohttp. Supports SSL/TLS
    configuration via cert files or PFX, and integrates with BasisCore's CMS-based
    message handling system.

    Attributes:
        LOGGER (str): Configuration key for custom logger
        ROUTER (str): Configuration key for custom router
        MIDDLEWARES (str): Configuration key for middleware list
        HANDLER_ARGS (str): Configuration key for handler arguments
        CLIENT_MAX_SIZE (str): Configuration key for max request size
        _DEFAULT_LOGGER: Default logger (aiohttp web_logger)
        _DEFAULT_ROUTER: Default router (None - uses wildcard)
        _DEFAULT_MIDDLEWARES: Default middleware tuple (empty)
        _DEFAULT_HANDLER_ARGS: Default handler args (None)
        _DEFAULT_CLIENT_MAX_SIZE (int): Default max size (1MB)
        _FILE_CHUNK_SIZE (int): Chunk size for file responses (256KB)

    Args:
        endpoint (Endpoint): Server endpoint (host:port)
        async_callback (Callable): Async message handler from dispatcher
        ssl_options (dict): SSL/TLS configuration (certfile/keyfile or pfxfile/password)
        configuration (Optional[DictEx]): Additional server configuration
        ws_manager (WebSocketSessionManager): WebSocket session manager

    Example:
        ```python
        # HTTP server
        listener = HttpListener(
            Endpoint("localhost:8080"),
            dispatcher.on_message_receive_async,
            ssl_options=None,
            configuration=None,
            ws_manager=ws_manager
        )

        # HTTPS server with cert files
        listener = HttpListener(
            Endpoint("0.0.0.0:443"),
            dispatcher.on_message_receive_async,
            ssl_options={
                "certfile": "/path/to/cert.pem",
                "keyfile": "/path/to/key.pem"
            },
            configuration=None,
            ws_manager=ws_manager
        )

        # HTTPS with PFX
        listener = HttpListener(
            Endpoint("0.0.0.0:443"),
            dispatcher.on_message_receive_async,
            ssl_options={
                "pfxfile": "/path/to/cert.pfx",
                "password": "secret"
            },
            configuration=None,
            ws_manager=ws_manager
        )
        ```
    """
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
    _FILE_CHUNK_SIZE = 256 * 1024  # 256 KB chunks for file responses

    def __init__(
        self,
        endpoint: Endpoint,
        async_callback: 'Callable[[Message], Awaitable[Message]]',
        logger: ILogger['HttpListener'],
        ssl_options: Optional[dict] = None,
        configuration: Optional[dict] = None,
        ws_manager: Optional['WebSocketSessionManager'] = None,
    ):
        """Initialize HTTP listener with endpoint and configuration

        Args:
            endpoint (Endpoint): Server binding (host:port)
            async_callback (Callable): Async message handler from dispatcher
            ssl_options (Optional[dict]): SSL/TLS config with certfile/keyfile or pfxfile/password
            configuration (Optional[DictEx]): Server config (logger, middlewares, etc.)
            ws_manager (Optional[WebSocketSessionManager]): WebSocket session manager instance
            logger (Optional[ILogger]): Logger instance (will be injected by DI if not provided)
        """
        self.__endpoint = endpoint
        self.__ssl_options = ssl_options
        self.__config = configuration if configuration is not None else DictEx()

        super().__init__(async_callback, logger)
        self.__router = self.__config.get(
            HttpListener.ROUTER, HttpListener._DEFAULT_ROUTER)
        self.__middlewares = self.__config.get(
            HttpListener.MIDDLEWARES, HttpListener._DEFAULT_MIDDLEWARES)
        self.__handler_args = self.__config.get(
            HttpListener.HANDLER_ARGS, HttpListener._DEFAULT_HANDLER_ARGS)
        self.__client_max_size = self.__config.get(
            HttpListener.CLIENT_MAX_SIZE, HttpListener._DEFAULT_CLIENT_MAX_SIZE)
        self.__ws_manager = ws_manager

    def initialize_task(self, event_loop: asyncio.AbstractEventLoop):
        """Initialize HTTP server task in event loop

        Args:
            event_loop (asyncio.AbstractEventLoop): Event loop to run server in
        """
        event_loop.create_task(self.__server_task(event_loop))

    async def __server_task(self, event_loop: asyncio.AbstractEventLoop):
        """Main server task that runs the HTTP/HTTPS server

        Sets up aiohttp web application with routing, SSL context, and starts
        the TCP site. Handles graceful shutdown on cancellation.

        Args:
            event_loop (asyncio.AbstractEventLoop): Event loop for server

        Notes:
            - Creates wildcard route that handles all paths
            - Supports both HTTP and HTTPS via ssl_options
            - Auto-detects WebSocket upgrade requests
            - Cleans up temporary SSL files from PFX conversion
        """
        from aiohttp import web

        async def on_request_receive_async(request: 'web.Request') -> web.Response:
            # Create CMS object from request
            cms_object = await WebRequestHelper.create_cms_async(request)

            # Check for WebSocket upgrade
            if request.headers.get('Upgrade', '').lower() == 'websocket':
                # Manager creates WebSocket, prepares it, and handles everything
                return await self.__ws_manager.handle_connection(request, cms_object)

            # Handle regular HTTP request
            return await self.__handle_http_async(request, cms_object)

        app = web.Application(
            logger=self._logger,
            router=self.__router,
            middlewares=self.__middlewares,
            handler_args=self.__handler_args,
            client_max_size=self.__client_max_size,
            loop=event_loop
        )
        app.add_routes(
            [web.route('*', '/{tail:.*}', on_request_receive_async)])
        ssl_context = None
        if self.__ssl_options:
            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            if "certfile" in self.__ssl_options:
                ssl_context.load_cert_chain(
                    certfile=self.__ssl_options["certfile"],
                    keyfile=self.__ssl_options["keyfile"]
                )
            elif "pfxfile" in self.__ssl_options:
                fullchain_path, key_path = HttpListener.convert_pfx_to_temp_files(
                    self.__ssl_options["pfxfile"],
                    self.__ssl_options["password"]
                )
                try:
                    ssl_context.load_cert_chain(
                        certfile=fullchain_path, keyfile=key_path)
                finally:
                    # حذف فایل‌های موقت بعد از load
                    try:
                        os.remove(fullchain_path)
                    except OSError:
                        pass
                    try:
                        os.remove(key_path)
                    except OSError:
                        pass

        runner = web.AppRunner(app, handle_signals=True)
        await runner.setup()
        site = web.TCPSite(runner, self.__endpoint.url,
                           self.__endpoint.port, ssl_context=ssl_context)
        await site.start()
        self._logger.info(
            f"Development Edge server started at http{'s' if self.__ssl_options else ''}://{self.__endpoint.url}:{self.__endpoint.port}")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            self._logger.info(
                f"Development Edge server for http{'s' if self.__ssl_options else ''}://{self.__endpoint.url}:{self.__endpoint.port} stopped.")
            await site.stop()
            await runner.cleanup()
            await runner.shutdown()

    async def __handle_http_async(self, request: 'web.Request', cms_object: dict) -> 'web.Response':
        """
        Handle HTTP request

        Args:
            request: aiohttp web request
            cms_object: CMS object created from request

        Returns:
            web.Response object
        """
        from aiohttp import web

        # Pass cms object directly without serialization overhead.
        msg = HttpMessage(cms_object, request)
        await self._on_message_receive(msg)

        # Check if handler used streaming response
        if msg.Response is not None:
            # Handler used streaming, return the StreamResponse directly
            return msg.Response

        # Use cms_object if HttpMessage, otherwise decode buffer
        cms_cms = msg.response_data[HttpBaseDataType.CMS]
        return self.__create_response_from_cms(cms_cms)

    def __create_response_from_cms(self, cms_cms: dict) -> 'web.Response':
        """
        Create HTTP response from CMS data

        Args:
            cms_cms: CMS data dictionary containing response information

        Returns:
            web.Response object
        """
        from aiohttp import web
        from multidict import MultiDict

        cms_cms_webserver = cms_cms[HttpBaseDataType.WEB_SERVER]
        index = cms_cms_webserver[HttpBaseDataName.INDEX]
        header_code: str = cms_cms_webserver[HttpBaseDataName.HEADER_CODE]
        mime = cms_cms_webserver[HttpBaseDataName.MIME]
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
                    chunk_size=HttpListener._FILE_CHUNK_SIZE,
                    status=int(header_code.split(' ')[0]),
                    headers=headers
                )
            except FileNotFoundError:
                ret_val = web.Response(
                    status=404,
                    reason="File not found"
                )
            except (OSError, PermissionError) as e:
                ret_val = web.Response(
                    status=500,
                    reason=f"File access error: {str(e)}"
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
