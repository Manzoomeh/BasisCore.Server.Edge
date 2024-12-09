import asyncio

from bclib.listener.stream_base_message import StreamBaseMessage

class EndPointMessage(StreamBaseMessage):
    def __init__(self, reader: 'asyncio.StreamReader', writer: 'asyncio.StreamWriter'):
        super().__init__(reader, writer)

    async def read_next_message_async(self) -> 'EndPointMessage':
        ret_val = EndPointMessage(self.reader, self.writer)
        await ret_val._fill_async()
        return ret_val  
