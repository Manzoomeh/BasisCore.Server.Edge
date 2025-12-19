"""
Context Package

Provides context classes for different types of request/connection handlers
in the BasisCore framework.

Features:
    - Base context classes (Context, CmsBaseContext, SourceContext)
    - HTTP contexts (HttpContext, RESTfulContext, WebSocketContext)
    - Source contexts (ClientSourceContext, ServerSourceContext)
    - Member contexts (SourceMemberContext, ClientSourceMemberContext, ServerSourceMemberContext)
    - Message queue context (RabbitContext)
    - Context merging utilities (MergeType)

Example:
    ```python
    from bclib.context import HttpContext, Context
    
    # HTTP request context
    async def handler(context: HttpContext):
        user_id = context.query.get('user_id')
        await context.send_json({'status': 'ok'})
    
    # WebSocket context
    async def ws_handler(context: WebSocketContext):
        await context.send('Hello WebSocket')
    ```
"""

from .client_source_context import ClientSourceContext
from .client_source_member_context import ClientSourceMemberContext
from .cms_base_context import CmsBaseContext
from .context import Context
from .context_factory import ContextFactory
from .http_context import HttpContext
from .merge_type import MergeType
from .rabbit_context import RabbitContext
from .restful_context import RESTfulContext
from .server_source_context import ServerSourceContext
from .server_source_member_context import ServerSourceMemberContext
from .source_context import SourceContext
from .source_member_context import SourceMemberContext
from .websocket_context import WebSocketContext

__all__ = [
    # Base contexts
    'Context',
    'CmsBaseContext',
    'SourceContext',
    'SourceMemberContext',

    # HTTP contexts
    'HttpContext',
    'RESTfulContext',
    'WebSocketContext',

    # Client source contexts
    'ClientSourceContext',
    'ClientSourceMemberContext',

    # Server source contexts
    'ServerSourceContext',
    'ServerSourceMemberContext',

    # Message queue context
    'RabbitContext',

    # Utilities
    'MergeType',
    'ContextFactory',
]
