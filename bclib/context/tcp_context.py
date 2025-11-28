"""
TCP Context - Context for TCP socket-based requests

This module provides the TcpContext class for handling TCP socket connections in the BasisCore.Server.Edge framework.
It extends CmsBaseContext to provide TCP-specific functionality for bidirectional binary protocol communication.

Key Features:
    - Raw TCP socket communication
    - Binary protocol support
    - Bidirectional data transmission
    - Session-based connection handling
    - Integration with CMS message format for structured data exchange

Example:
    ```python
    @app.tcp_action(app.url("tcp/command"))
    async def tcp_handler(context: TcpContext):
        # Access TCP message
        message = context.message
        
        # Read incoming data
        data = message.data
        
        # Send response back through TCP socket
        response_data = process_command(data)
        await message.send(response_data)
        
        # Access connection info
        client_address = message.client_address
        session_id = message.session_id
    ```
    
Note:
    TCP connections use binary protocols and require proper message framing.
    The TcpMessage handles the low-level socket operations while TcpContext
    provides the high-level request/response abstraction.
"""
from typing import TYPE_CHECKING

from bclib.context.cms_base_context import CmsBaseContext

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher
    from bclib.listener.tcp.tcp_message import TcpMessage


class TcpContext(CmsBaseContext):
    """
    Context class for TCP socket-based requests

    Provides TCP-specific functionality for handling raw socket connections with
    binary protocol support. Each TCP connection creates a new context with access
    to the underlying socket message for bidirectional communication.

    Attributes:
        message (TcpMessage): The TCP message object containing socket data and connection info

    Args:
        cms_object: CMS object containing request data parsed from TCP payload
        dispatcher: Dispatcher instance for routing and handling
        message: TCP message instance from the listener

    Example:
        ```python
        @app.tcp_action(app.url("tcp/data"))
        async def handle_tcp_data(context: TcpContext):
            # Parse incoming data
            command = context.cms.get('command')
            params = context.cms.get('params', {})

            # Process command
            result = await process_tcp_command(command, params)

            # Send response
            await context.message.send_json(result)
        ```

    Note:
        Unlike HTTP contexts, TCP contexts work with persistent connections.
        The socket remains open until explicitly closed or disconnected.
    """

    def __init__(self, cms_object: dict,  dispatcher: 'IDispatcher', message: 'TcpMessage') -> None:
        """
        Initialize TCP context

        Args:
            cms_object: CMS object containing parsed TCP request data
            dispatcher: Dispatcher instance for routing
            message: TCP message instance containing socket connection and data

        Note:
            The context is created with create_scope=True to ensure proper
            dependency injection scoping for each TCP request.
        """
        super().__init__(cms_object, dispatcher, True)
        self.message: 'TcpMessage' = message
