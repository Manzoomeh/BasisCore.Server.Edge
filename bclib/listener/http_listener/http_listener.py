import asyncio
import ssl
from typing import Callable, TYPE_CHECKING, Coroutine, Optional
from ..endpoint import Endpoint
from bclib.utility import DictEx
from ..web_message import WebMessage

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
    

    def __init__(self, endpoint: Endpoint, async_callback: 'Callable[[WebMessage],Coroutine]',ssl_options:'dict', configuration: Optional[DictEx]):
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
        async def on_request_receive_async(request: 'web.Request') -> web.Response:
            msg = WebMessage(request)
            await self.on_message_receive_async(msg)
            return msg.Response

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
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            print(f"Development Edge server for http{'s' if self.ssl_options else ''}://{self.__endpoint.url}:{self.__endpoint.port} stopped.")
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