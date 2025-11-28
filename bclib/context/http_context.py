"""
HTTP Context - Context for HTTP-based requests

This module provides the HttpContext class for handling HTTP requests in the BasisCore.Server.Edge framework.
It extends CmsBaseContext to provide HTTP-specific functionality including streaming responses,
compression, and chunked data transmission.

Key Features:
    - Streaming response support for large datasets
    - Built-in compression (gzip, deflate, brotli)
    - Chunked data transmission for memory-efficient processing
    - Async/await support for non-blocking I/O operations

Example:
    ```python
    @app.http_action(app.url("api/data"))
    async def stream_handler(context: HttpContext):
        # Start streaming response
        await context.start_stream_response_async(status=200)
        
        # Enable compression
        await context.enable_compression()
        
        # Stream large dataset in chunks
        large_data = get_large_dataset()
        await context.drain_array_async(
            data_list=large_data,
            source_name="users",
            chunk_size=1000
        )
    ```
"""
import json
from itertools import islice
from typing import TYPE_CHECKING, Any, Coroutine, Iterator, Optional, Union

from aiohttp.web_response import ContentCoding

from bclib.context.cms_base_context import CmsBaseContext

if TYPE_CHECKING:
    from bclib.dispatcher.idispatcher import IDispatcher
    from bclib.listener.http.http_message import HttpMessage


class HttpContext(CmsBaseContext):
    """
    Context class for HTTP-based requests

    Provides HTTP-specific functionality for handling web requests including
    streaming responses, compression, and efficient data transmission.

    Attributes:
        process_async (bool): Indicates this context supports async processing

    Args:
        cms_object: CMS object containing request data
        dispatcher: Dispatcher instance for routing and handling
        message_object: HTTP message object from the listener
    """

    def __init__(self, cms_object: dict,  dispatcher: 'IDispatcher', message_object: 'HttpMessage') -> None:
        super().__init__(cms_object, dispatcher, True)
        self.process_async = True
        self.__message = message_object

    async def start_stream_response_async(self, status: int = 200,
                                          reason: Optional[str] = 'OK',
                                          headers: Optional[dict] = None,) -> Coroutine[Any, Any, None]:
        """
        Start a streaming HTTP response

        Initializes a streaming response with the specified status code, reason phrase,
        and headers. Use this when you need to send data in chunks rather than all at once.

        Args:
            status: HTTP status code (default: 200)
            reason: HTTP reason phrase (default: 'OK')
            headers: Optional dictionary of HTTP headers

        Example:
            ```python
            await context.start_stream_response_async(
                status=200,
                headers={'Content-Type': 'application/json'}
            )
            ```
        """
        await self.__message.start_stream_response_async(status, reason, headers)

    async def write_async(self, data: 'bytes') -> Coroutine[Any, Any, None]:
        """
        Write data to the streaming response

        Sends a chunk of data to the client. Must call start_stream_response_async first.

        Args:
            data: Bytes to write to the response stream

        Example:
            ```python
            await context.write_async(b'{"status": "processing"}')
            ```
        """
        await self.__message.write_async(data)

    async def drain_async(self) -> Coroutine[Any, Any, None]:
        """
        Drain the response buffer

        Ensures all buffered data is sent to the client. Should be called after
        write_async to flush the buffer.

        Example:
            ```python
            await context.write_async(data)
            await context.drain_async()
            ```
        """
        await self.__message.drain_async()

    async def write_and_drain_async(self, data: 'bytes') -> Coroutine[Any, Any, None]:
        """
        Write data and immediately drain the buffer

        Convenience method that combines write_async and drain_async.

        Args:
            data: Bytes to write and flush to the response stream

        Example:
            ```python
            await context.write_and_drain_async(b'{"chunk": 1}')
            ```
        """
        await self.write_async(data)
        await self.drain_async()

    async def enable_compression(self, force: Optional[Union[bool, ContentCoding]] = None) -> None:
        """
        Enable HTTP response compression

        Enables compression (gzip, deflate, or brotli) based on client's Accept-Encoding
        header or force a specific compression algorithm.

        Args:
            force: Optional compression type to force:
                   - True: Auto-select based on Accept-Encoding
                   - ContentCoding.gzip: Force gzip compression
                   - ContentCoding.deflate: Force deflate compression
                   - ContentCoding.brotli: Force brotli compression

        Example:
            ```python
            # Auto-select compression
            await context.enable_compression()

            # Force gzip
            from aiohttp.web_response import ContentCoding
            await context.enable_compression(ContentCoding.gzip)
            ```
        """
        await self.__message.enable_compression(force)

    async def drain_array_async(self, data_list: Iterator, source_name: str, chunk_size: int, delimiter: str = ',') -> Coroutine[Any, Any, None]:
        """
        Stream large arrays in chunks

        Efficiently streams large datasets by breaking them into chunks and sending
        them incrementally. Ideal for memory-efficient processing of big data.

        Args:
            data_list: Iterator or list containing data to stream
            source_name: Name of the data source (used in response structure)
            chunk_size: Number of items to send per chunk
            delimiter: String delimiter between chunks (default: ',')

        Example:
            ```python
            large_dataset = get_users()  # Returns 1 million records

            await context.start_stream_response_async()
            await context.drain_array_async(
                data_list=large_dataset,
                source_name="users",
                chunk_size=1000,  # Send 1000 records at a time
                delimiter=','
            )
            ```

        Note:
            Each chunk is wrapped in a BasisCore CMS format with source metadata.
            The mergeType is set to 1 (append) for proper client-side handling.
        """
        total_len = len(data_list)
        current: int = 0
        while current < total_len:
            temp_list = list(islice(data_list, current, current + chunk_size))
            current += len(temp_list)
            data = {
                "sources": [
                    {
                        "options": {
                            "tableName": source_name,
                            "mergeType": 1  # MergeType append,
                        },
                        "data": temp_list
                    }],
            }
            await self.write_and_drain_async(f"{json.dumps(data)}{delimiter}".encode())
