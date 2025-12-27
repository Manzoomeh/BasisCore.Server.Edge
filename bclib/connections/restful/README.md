# RESTful HTTP Connection Module

Modern async HTTP client for BasisCore.Edge with **certifi SSL verification** and **automatic error handling**.

## Features

✅ **All HTTP Methods**: GET, POST, PUT, PATCH, DELETE  
✅ **Automatic Response Parsing**: JSON with fallback to text  
✅ **HTTP Error Handling**: `raise_for_status` parameter (default: True)  
✅ **SSL Verification**: Uses certifi CA bundle for cross-platform reliability  
✅ **Session Pooling**: Efficient connection reuse with aiohttp  
✅ **Type-Safe**: ILogger<T>-style generic configuration  
✅ **No Inheritance**: Inject IRestfulConnection[TConfig] directly

## Quick Start

### 1. Configuration (host.json)

```json
{
  "external_api": {
    "base_url": "https://api.example.com",
    "timeout": 30,
    "headers": {
      "Authorization": "Bearer your-token-here",
      "Content-Type": "application/json"
    },
    "ssl_verify": true
  },

  "internal_api": {
    "base_url": "http://localhost:8080",
    "timeout": 10,
    "ssl_verify": false
  }
}
```

### 2. Register Service

```python
from bclib.connections.restful import add_restful_connection
from bclib.options import add_options_service

# In your startup code
add_options_service(service_provider, config)
add_restful_connection(service_provider)
```

### 3. Use in Your Service

```python
from bclib.connections.restful import IRestfulConnection

class UserService:
    def __init__(self, api: IRestfulConnection['external_api']):
        self.api = api

    async def get_users(self):
        # Automatically parses JSON and raises for HTTP errors
        return await self.api.get_async('/users')

    async def create_user(self, name: str, email: str):
        return await self.api.post_async(
            '/users',
            json={'name': name, 'email': email}
        )

    async def update_user(self, user_id: str, data: dict):
        return await self.api.put_async(f'/users/{user_id}', json=data)

    async def delete_user(self, user_id: str):
        return await self.api.delete_async(f'/users/{user_id}')
```

## HTTP Methods

### GET Request

```python
# Simple GET
users = await api.get_async('/users')

# GET with query parameters
users = await api.get_async('/users', params={'page': 1, 'limit': 10})

# GET with custom headers
users = await api.get_async('/users', headers={'X-Custom': 'value'})

# GET without automatic error checking
response = await api.get_async('/users', raise_for_status=False)
```

### POST Request

```python
# POST with JSON body
user = await api.post_async('/users', json={'name': 'John', 'email': 'john@example.com'})

# POST with form data
result = await api.post_async('/upload', data={'file': file_content})

# POST without error checking
result = await api.post_async('/users', json=data, raise_for_status=False)
```

### PUT Request

```python
updated_user = await api.put_async(
    '/users/123',
    json={'name': 'John Updated', 'email': 'new@example.com'}
)
```

### PATCH Request

```python
patched_user = await api.patch_async(
    '/users/123',
    json={'name': 'John Patched'}
)
```

### DELETE Request

```python
# DELETE with auto error checking
result = await api.delete_async('/users/123')

# DELETE with query params
result = await api.delete_async('/users/123', params={'force': 'true'})
```

## Configuration Options

| Option          | Type   | Default      | Description                          |
| --------------- | ------ | ------------ | ------------------------------------ |
| `base_url`      | string | **required** | Base URL for all requests            |
| `timeout`       | int    | 30           | Request timeout in seconds           |
| `headers`       | dict   | {}           | Default headers for all requests     |
| `ssl_verify`    | bool   | true         | Enable SSL certificate verification  |
| `ssl_cert_path` | string | null         | Path to custom CA certificate bundle |

## SSL Configuration

### Default (certifi)

Uses certifi CA bundle for reliable cross-platform SSL verification:

```json
{
  "api": {
    "base_url": "https://api.example.com",
    "ssl_verify": true
  }
}
```

### Custom Certificate

Use your own CA certificate:

```json
{
  "api": {
    "base_url": "https://api.example.com",
    "ssl_cert_path": "/path/to/ca-bundle.crt"
  }
}
```

### Disable SSL (Development Only)

**⚠️ Not recommended for production!**

```json
{
  "api": {
    "base_url": "https://api.example.com",
    "ssl_verify": false
  }
}
```

## Error Handling

### Automatic (Default)

By default, HTTP errors (status >= 400) raise exceptions:

```python
try:
    user = await api.get_async('/users/999')  # 404 Not Found
except Exception as e:
    print(f"Error: {e}")  # "GET failed: status=404 url=users/999 response=..."
```

### Manual

Disable automatic error checking:

```python
response = await api.get_async('/users/999', raise_for_status=False)
if response:
    # Handle response
else:
    # Handle error manually
```

## Response Parsing

The module automatically parses responses:

1. **Try JSON first** (regardless of content-type header)
2. **Fallback to text** if JSON parsing fails

This handles APIs that:

- Return JSON without proper content-type headers
- Return non-JSON error messages
- Mix JSON and plain text responses

```python
# These all work automatically:
user_dict = await api.get_async('/users/1')           # Returns dict
users_list = await api.get_async('/users')            # Returns list
html_text = await api.get_async('/legacy-endpoint')   # Returns string
```

## Advanced Usage

### Multiple API Connections

```python
class MultiApiService:
    def __init__(
        self,
        external_api: IRestfulConnection['external_api'],
        internal_api: IRestfulConnection['internal_api']
    ):
        self.external = external_api
        self.internal = internal_api

    async def sync_data(self):
        # Fetch from external API
        data = await self.external.get_async('/data')

        # Push to internal API
        result = await self.internal.post_async('/sync', json=data)

        return result
```

### Custom Headers per Request

```python
class AuthenticatedService:
    def __init__(self, api: IRestfulConnection['api']):
        self.api = api
        self.token = None

    async def login(self, username: str, password: str):
        self.token = await self.api.post_async(
            '/auth/login',
            json={'username': username, 'password': password}
        )

    async def get_protected_resource(self):
        # Add auth header to this request only
        return await self.api.get_async(
            '/protected',
            headers={'Authorization': f'Bearer {self.token}'}
        )
```

### Cleanup

```python
class MyService:
    def __init__(self, api: IRestfulConnection['api']):
        self.api = api

    async def close(self):
        # Clean up resources
        await self.api.close_async()
```

## Testing

Run the test suite:

```bash
python test/restful/test_restful_enhanced.py
```

The test demonstrates:

- ✅ GET with automatic JSON parsing
- ✅ POST with JSON body
- ✅ GET with query parameters
- ✅ Automatic error raising (404)
- ✅ Manual error handling with raise_for_status=False
- ✅ PUT request
- ✅ PATCH request
- ✅ DELETE request
- ✅ certifi SSL verification

## Comparison with Legacy Code

### Before (Legacy)

```python
class OldService(Db):  # Inheritance required
    def __init__(self, *args):
        super().__init__(*args)

    async def get_users(self):
        async with aiohttp.ClientSession() as session:  # New session every call
            async with session.get(url) as response:
                return await self.__read_json_or_text(response)
```

### After (Modern)

```python
class NewService:
    def __init__(self, api: IRestfulConnection['api']):  # No inheritance
        self.api = api

    async def get_users(self):
        return await self.api.get_async('/users')  # Session pooling + auto parsing
```

## Benefits

| Feature              | Legacy                  | Modern                     |
| -------------------- | ----------------------- | -------------------------- |
| **Inheritance**      | Required (Db)           | ❌ None required           |
| **Session Pooling**  | ❌ New session per call | ✅ Shared session          |
| **SSL Verification** | ⚠️ System default       | ✅ certifi CA bundle       |
| **Error Handling**   | Manual                  | ✅ Automatic with override |
| **Response Parsing** | Manual                  | ✅ Automatic JSON/text     |
| **Type Safety**      | ❌ None                 | ✅ Generic types           |
| **Configuration**    | Hardcoded               | ✅ host.json               |
| **HTTP Methods**     | GET, POST only          | ✅ All methods             |
| **DI Integration**   | ❌ Limited              | ✅ Full support            |

## Dependencies

- **aiohttp**: Async HTTP client
- **certifi**: CA certificate bundle (install with `pip install certifi`)

## Notes

- The module uses **lazy initialization** for ClientSession (created on first use)
- SSL context uses **certifi by default** for cross-platform reliability
- Responses are **automatically parsed** (JSON with fallback to text)
- HTTP errors (status >= 400) **raise exceptions by default**
- All HTTP methods support **custom headers** and **raise_for_status** parameter

## Migration from Legacy Code

If you have legacy code using the old pattern:

1. **Remove inheritance** from Db class
2. **Inject** IRestfulConnection['your_api'] in constructor
3. **Replace** manual aiohttp calls with api methods
4. **Remove** manual error checking (or use raise_for_status=False)
5. **Remove** manual JSON parsing (handled automatically)

Example migration:

```python
# Before
class UserService(Db):
    async def get_users(self):
        url = f"{self.base_url}/users"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status >= 400:
                    raise Exception(f"Error: {response.status}")
                return await response.json()

# After
class UserService:
    def __init__(self, api: IRestfulConnection['external_api']):
        self.api = api

    async def get_users(self):
        return await self.api.get_async('/users')
```

---

**Made with ❤️ for BasisCore.Edge**
