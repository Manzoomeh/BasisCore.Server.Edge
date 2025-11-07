"""Web Request Helper - utilities for processing web requests"""
import base64
import datetime
from typing import TYPE_CHECKING
from urllib.parse import parse_qs

from bclib.listener.http_listener.http_base_data_name import HttpBaseDataName
from bclib.listener.http_listener.http_base_data_type import HttpBaseDataType

if TYPE_CHECKING:
    from aiohttp import web


class WebRequestHelper:
    """Helper class for processing web.Request and creating CMS objects"""

    _request_id = 0

    @staticmethod
    async def create_cms_async(request: 'web.Request') -> dict:
        """
        Create CMS object from web.Request

        Args:
            request: aiohttp web request

        Returns:
            dict: CMS object with request data
        """
        from urllib.parse import unquote

        cms_object = dict()
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.METHODE, request.method.lower())
        raw_url = unquote(request.path_qs)[1:]
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.RAW_URL, raw_url)
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.URL, request.path[1:])
        WebRequestHelper.__add_query_string(request.query, cms_object)
        for key, value in request.headers.items():
            field_name = key.strip().lower()
            if field_name == HttpBaseDataName.COOKIE:
                WebRequestHelper.__add_cookie(value, cms_object)
            elif field_name == HttpBaseDataName.HOST:
                WebRequestHelper.__add_host(value, raw_url, cms_object)
            else:
                WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                              field_name, str(value).strip())
        WebRequestHelper.__add_server_data(cms_object, request)
        await WebRequestHelper.__add_body_async(cms_object, request)
        return {"cms": cms_object}

    @staticmethod
    async def __add_body_async(cms_object: dict, request: 'web.Request'):
        """Add request body to CMS object"""
        content_len_str = request.headers.get('Content-Length')
        if not (content_len_str or request.can_read_body):
            return

        content_type: str = request.headers.get("content-type", "") or ""

        # Multipart handling (streaming) -------------------------------------------------
        if content_type.startswith("multipart/"):
            # Use aiohttp's multipart reader to get proper filenames & headers
            try:
                reader = await request.multipart()
            except Exception:
                # Fallback: read raw so that at least body captured
                raw_body = await request.read()
                WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                              HttpBaseDataName.BODY, f"[multipart raw size={len(raw_body)}]")
                return

            # Collect file parts as a flat list instead of dict keyed by field name
            files_node = []
            form_fields_collected = {}
            part_index = 0
            async for part in reader:
                part_index += 1
                cd = part.headers.get('Content-Disposition', '')
                # Extract name & filename from content-disposition manually (lightweight)
                field_name = None
                file_name = None
                if cd:
                    for item in cd.split(';'):
                        item = item.strip()
                        if item.startswith('name='):
                            field_name = item[5:].strip().strip('"')
                        elif item.startswith('filename='):
                            file_name = item[9:].strip().strip('"')
                if field_name is None:
                    field_name = f"part_{part_index}"

                if file_name:
                    # It's a file part
                    data = await part.read(decode=False)
                    file_record = {
                        "field": field_name,
                        "name": file_name,
                        "size": len(data),
                        "content_type": part.headers.get('Content-Type') or '',
                        "content": data
                    }
                    files_node.append(file_record)
                else:
                    # Regular form field (text) - attempt utf-8 decode
                    try:
                        value_text = (await part.text())
                    except UnicodeDecodeError:
                        raw_val = await part.read(decode=False)
                        value_text = base64.b64encode(raw_val).decode('utf-8')
                    prev = form_fields_collected.get(field_name)
                    if prev is None:
                        form_fields_collected[field_name] = value_text
                    else:
                        if isinstance(prev, list):
                            prev.append(value_text)
                        else:
                            form_fields_collected[field_name] = [
                                prev, value_text]

            # Add form fields
            for k, v in form_fields_collected.items():
                WebRequestHelper.__add_header(
                    cms_object, HttpBaseDataType.FORM, k, v)
            # Add files node if present
            if files_node:
                cms_object['files'] = files_node
            # Store safe body summary
            WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                          HttpBaseDataName.BODY, f"[multipart parts={part_index} files={len(files_node)}]")
            return

        # Non-multipart ---------------------------------------------------------------
        raw_body = await request.read()
        if not raw_body:
            WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                          HttpBaseDataName.BODY, "")
            return

        # JSON or form or binary fallback
        if content_type.startswith('application/json'):
            try:
                text_body = raw_body.decode('utf-8')
            except UnicodeDecodeError:
                text_body = base64.b64encode(raw_body).decode('utf-8')
            WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                          HttpBaseDataName.BODY, text_body)
            return

        # application/x-www-form-urlencoded or others treat as form attempt
        try:
            text_body = raw_body.decode('utf-8')
            if content_type.startswith('application/x-www-form-urlencoded'):
                for key, value in parse_qs(text_body).items():
                    WebRequestHelper.__add_header(cms_object, HttpBaseDataType.FORM, key,
                                                  value[0] if len(value) == 1 else value)
            WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                          HttpBaseDataName.BODY, text_body)
        except UnicodeDecodeError:
            # Binary fallback
            WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                          HttpBaseDataName.BODY, base64.b64encode(raw_body).decode('utf-8'))

    @staticmethod
    def __add_server_data(cms_object: dict, request: 'web.Request'):
        """Add server and request metadata to CMS object"""
        WebRequestHelper._request_id += 1
        now = datetime.datetime.now()
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.CMS,
                                      HttpBaseDataName.DATE, now.strftime("%d/%m/%Y"))
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.CMS,
                                      HttpBaseDataName.TIME, now.strftime("%H:%M"))
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.CMS,
                                      HttpBaseDataName.DATE2, now.strftime("%Y%m%d"))
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.CMS,
                                      HttpBaseDataName.TIME2, now.strftime("%H%M%S"))
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.CMS,
                                      HttpBaseDataName.DATE3, now.strftime("%Y.%m.%d"))
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.REQUEST_ID, str(WebRequestHelper._request_id))
        host_parts = request.host.split(':')
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.HOST_IP, host_parts[0])
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.HOST_PORT,  host_parts[1] if len(host_parts) > 1 else "80")
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.CLIENT_IP, str(request.remote))

    @staticmethod
    def __add_query_string(query: dict, cms_object: dict) -> None:
        """Add query string parameters to CMS object"""
        for key, value in query.items():
            WebRequestHelper.__add_header(
                cms_object, HttpBaseDataType.QUERY, key, value)

    @staticmethod
    def __add_cookie(raw_header_value: str, cms_object) -> None:
        """Add cookie values to CMS object"""
        for item in raw_header_value.split(';'):
            parts = item.split('=')
            if len(parts) == 2:
                WebRequestHelper.__add_header(cms_object, HttpBaseDataName.COOKIE,
                                              parts[0].strip(), parts[1].strip())

    @staticmethod
    def __add_host(row_host: str, row_url: str, cms_object) -> None:
        """Add host information to CMS object"""
        host_parts = row_host.split(':')
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.HOST, host_parts[0])
        if len(host_parts) == 2:
            WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                          HttpBaseDataName.PORT, host_parts[1])
        WebRequestHelper.__add_header(cms_object, HttpBaseDataType.REQUEST,
                                      HttpBaseDataName.FULL_URL,  f"{row_host}/{row_url}")

    @staticmethod
    def __add_header(cms_object: dict, value_type: str, value_name: str, value: str) -> None:
        """Add a header value to CMS object"""
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
