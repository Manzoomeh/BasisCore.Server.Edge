"""
BasisCore Edge - Main module for creating dispatcher instances and starting servers

This module provides the main entry points for creating and configuring BasisCore.Server.Edge
applications. It handles initialization of dispatchers, listeners (HTTP, WebSocket, TCP, RabbitMQ),
and server startup with various configuration options.

Key Features:
    - Multiple listener types: HTTP/HTTPS, WebSocket, TCP Socket, RabbitMQ
    - Flexible configuration via JSON files or dictionaries
    - Multi-instance deployment support
    - Automatic listener creation based on configuration
    - Built-in dependency injection support

Main Functions:
    - from_options(): Create dispatcher from configuration dictionary (recommended)
    - from_config(): Load configuration from JSON file and create dispatcher
    - from_list(): Run multiple instances with different configurations

Example:
    ```python
    from bclib import edge
    
    # Simple HTTP server
    options = {
        "http": "localhost:8080",
        "router": "restful"
    }
    app = edge.from_options(options)
    
    # Register handlers
    @app.restful_handler(app.url("api/hello"))
    def hello_handler(context: edge.RESTfulContext):
        return {"message": "Hello World"}
    
    # Start server
    app.listening()
    ```
"""

import asyncio

from bclib import __version__
from bclib.context import *
from bclib.db_manager import *
from bclib.dispatcher import IDispatcher, adding_dispatcher_services
from bclib.exception import *
from bclib.listener import (HttpBaseDataName, HttpBaseDataType, Message,
                            MessageType)
from bclib.log_service import ILogService, add_log_service
from bclib.logger import ILogger, add_default_logger
from bclib.options import IOptions, add_options_service
from bclib.predicate import Predicate, PredicateHelper
from bclib.service_provider import IServiceProvider, create_service_provider
from bclib.utility import (DictEx, HttpHeaders, HttpMimeTypes, HttpStatusCodes,
                           ResponseTypes, StaticFileHandler)


def from_config(option_file_path: str, file_name: str = "host.json") -> IDispatcher:
    """
    Create Dispatcher from JSON configuration file

    Loads configuration from a JSON file and creates a dispatcher instance.
    This is a convenience method for file-based configuration.

    Args:
        option_file_path: Path to the directory containing the config file
        file_name: Name of the JSON configuration file (default: "host.json")

    Returns:
        Dispatcher: Configured dispatcher instance

    Example:
        ```python
        from bclib import edge

        # Load from host.json in config directory
        app = edge.from_config("./config")

        # Or specify custom filename
        app = edge.from_config("./config", "production.json")
        ```
    """
    import json
    from pathlib import Path

    with open(Path(option_file_path).with_name(file_name), encoding="utf-8") as options_file:
        options = json.load(options_file)
    return from_options(options)


def from_list(hosts: 'dict[str,list[str]]') -> None:
    """
    Run multiple server instances with different configurations

    Creates and runs multiple dispatcher instances in parallel, each with its own
    configuration. Useful for running multiple services or environments simultaneously.

    Args:
        hosts: Dictionary mapping host names to their configuration arguments
               Format: {"host_name": ["arg1", "arg2", ...]}

    Example:
        ```python
        from bclib import edge

        hosts = {
            "api_server": ["python", "api_app.py"],
            "web_server": ["python", "web_app.py"],
        }
        edge.from_list(hosts)
        ```
    """
    import concurrent.futures
    import subprocess

    __print_splash(True)
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(hosts.items())) as executor:
        tasks: list[asyncio.Future] = []
        for host, args in hosts.items():
            args.append(f"-n {host}")
            args.append("-m")
            tasks.append(loop.run_in_executor(executor, subprocess.run, args))
            print(f'{host} start running from {args[1]}')
        loop.run_until_complete(asyncio.gather(*tasks))


def from_options(options: dict, loop: asyncio.AbstractEventLoop = None) -> IDispatcher:
    """
    Create Dispatcher with listeners based on configuration dictionary

    This is the main entry point for creating BasisCore applications. It creates a
    Dispatcher instance and automatically configures appropriate listeners based on
    the provided options.

    Supported Configuration Keys:
        - http: HTTP/HTTPS server endpoint (e.g., "localhost:8080")
        - tcp: TCP socket endpoint (e.g., "localhost:3000")
        - router: Routing configuration (string or dict)
        - ssl: SSL/TLS configuration for HTTPS
        - configuration: Additional HTTP server configuration
        - name: Application name for logging
        - log_error: Enable error logging (default: False)
        - log_request: Enable request logging (default: True)
        - cache: Cache configuration
        - logger: Logging configuration

    Args:
        options: Configuration dictionary with server settings
        loop: Optional asyncio event loop (creates new one if not provided)

    Returns:
        Dispatcher: Configured dispatcher ready for handler registration

    Example:
        ```python
        from bclib import edge

        # Minimal HTTP server
        options = {
            "http": "localhost:8080",
            "router": "restful"
        }
        app = edge.from_options(options)

        # Full configuration
        options = {
            "name": "MyAPI",
            "http": "0.0.0.0:443",
            "ssl": {
                "cert": "/path/to/cert.pem",
                "key": "/path/to/key.pem"
            },
            "router": {
                "restful": ["api/*"],
                "web": ["*"]
            },
            "tcp": "localhost:3000",
            "log_request": True,
            "log_error": True
        }
        app = edge.from_options(options)

        @app.restful_handler(app.url("api/users"))
        def get_users():
            return {"users": []}

        app.listening()
        ```
    """
    import getopt
    import sys

    multi: bool = False
    argumentList = sys.argv[1:]
    # Options
    short_options = "mn:"
    # Long options
    long_options = ["Name =", "Multi"]
    try:
        arguments, _ = getopt.gnu_getopt(
            argumentList, short_options, long_options)
        for current_argument, current_value in arguments:
            if current_argument in ("-n", "--Name"):
                options["name"] = current_value.strip()
            elif current_argument in ("-m", "--Multi"):
                multi = True
    except getopt.error as err:
        print(str(err))

    if not multi:
        __print_splash(False)

    # Create ServiceProvider and set up event loop
    service_provider = create_service_provider(loop)
    add_default_logger(service_provider)

    # Register IOptions factory for configuration access
    add_options_service(service_provider, options)

    # Register log service in DI container
    add_log_service(service_provider)

    # Register database manager in DI container
    from bclib.db_manager import DbManager, IDbManager
    service_provider.add_singleton(IDbManager, DbManager)

    # Register listener factory in DI container
    from bclib.listener import adding_listener_services
    adding_listener_services(service_provider)

    adding_dispatcher_services(service_provider)

    # Create Dispatcher instance
    return service_provider.get_service(IDispatcher)


def __print_splash(inMultiMode: bool):
    print(f'''
______           _                          _____    _            
| ___ \\         (_)                        |  ___|  | |           
| |_/ / __ _ ___ _ ___  ___ ___  _ __ ___  | |__  __| | __ _  ___ 
| ___ \\/ _` / __| / __|/ __/ _ \\| '__/ _ \\ |  __|/ _` |/ _` |/ _ \\
| |_/ / (_| \\__ \\ \\__ \\ (_| (_) | | |  __/ | |__| (_| | (_| |  __/
\\____/ \\__,_|___/_|___/\\___\\___/|_|  \\___| \\____/\\__,_|\\__, |\\___|
                                                        __/ |     
                                                       |___/      
***********************************
Basiscore Edge

Welcome To BasisCore Ecosystem
Follow us on https://BasisCore.com/
bclib Version : {__version__}
Run in {'multi' if inMultiMode else 'single'} instance mode!
***********************************
(Press CTRL+C to quit)
''')
