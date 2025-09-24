from bclib.listener.stream_base_message import StreamBaseMessage

import asyncio

class SocketMessage(StreamBaseMessage):
     def __init__(self, reader: 'asyncio.StreamReader', writer: 'asyncio.StreamWriter'):
         super().__init__(reader, writer)