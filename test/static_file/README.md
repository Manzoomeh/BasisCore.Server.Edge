# Static File Handler

A secure and flexible static file server for BasisCore.Server.Edge that maps URL paths to file system directories.

## Features

✅ **URL to File Path Mapping** - Maps URL segments to directory structure  
✅ **Security** - Prevents path traversal attacks (`../`, `..\\`)  
✅ **MIME Type Detection** - Automatic content-type headers  
✅ **Index File Support** - Serves `index.html` for directory requests  
✅ **Extension Whitelisting** - Optional file type restrictions  
✅ **URL Prefix Support** - Mount static files at specific paths  

## Installation

The `StaticFileHandler` is included in `bclib.utility`:

```python
from bclib.utility import StaticFileHandler
```

## Quick Start

### Basic Usage

```python
from bclib import edge
from bclib.context import RESTfulContext
from bclib.utility import StaticFileHandler

app = edge.from_options({
    "server": {"url": "localhost", "port": 2022}
})

# Create handler
static_handler = StaticFileHandler(
    base_dir='./public',
    allowed_extensions={'.html', '.css', '.js', '.png', '.jpg'},
    enable_index=True
)

@app.restful_handler()
async def serve_static(context: RESTfulContext):
    await static_handler.handle(context)

app.run()
```

### With URL Prefix

```python
# Serve files from ./assets with /static prefix
static_handler = StaticFileHandler(
    base_dir='./assets',
    url_prefix='/static'
)

@app.restful_handler("/static/*")
async def serve_static(context: RESTfulContext):
    await static_handler.handle(context)
```

**URL Mapping:**
- `GET /static/style.css` → `./assets/style.css`
- `GET /static/images/logo.png` → `./assets/images/logo.png`

## Configuration Options

### `__init__` Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_dir` | `str` | (required) | Root directory for static files |
| `allowed_extensions` | `Set[str]` or `None` | `None` | Allowed file extensions (with dot). `None` = all allowed |
| `enable_index` | `bool` | `True` | Serve index files for directory requests |
| `index_files` | `List[str]` | `['index.html', 'index.htm']` | Index file names to try |
| `url_prefix` | `str` | `""` | URL prefix to strip before mapping |

## Examples

### Example 1: Serve HTML/CSS/JS

```python
static_handler = StaticFileHandler(
    base_dir='./public',
    allowed_extensions={'.html', '.css', '.js', '.json'},
    enable_index=True
)
```

**Directory Structure:**
```
public/
├── index.html
├── css/
│   └── style.css
└── js/
    └── app.js
```

**URLs:**
- `GET /` → `./public/index.html`
- `GET /css/style.css` → `./public/css/style.css`
- `GET /js/app.js` → `./public/js/app.js`

### Example 2: Serve Images

```python
image_handler = StaticFileHandler(
    base_dir='./images',
    allowed_extensions={'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'},
    enable_index=False,
    url_prefix='/images'
)

@app.restful_handler("/images/*")
async def serve_images(context: RESTfulContext):
    await image_handler.handle(context)
```

**URLs:**
- `GET /images/logo.png` → `./images/logo.png`
- `GET /images/icons/home.svg` → `./images/icons/home.svg`

### Example 3: Multiple Static Directories

```python
# Serve web assets
web_handler = StaticFileHandler(
    base_dir='./public',
    allowed_extensions={'.html', '.css', '.js'}
)

# Serve media files
media_handler = StaticFileHandler(
    base_dir='./media',
    allowed_extensions={'.png', '.jpg', '.mp4', '.mp3'},
    url_prefix='/media'
)

@app.restful_handler()
async def serve_web(context: RESTfulContext):
    await web_handler.handle(context)

@app.restful_handler("/media/*")
async def serve_media(context: RESTfulContext):
    await media_handler.handle(context)
```

## Security

### Path Traversal Prevention

The handler automatically prevents path traversal attacks:

```python
# These will return 403 Forbidden:
GET /../../../etc/passwd
GET /..\\..\\windows\\system32\\config\\sam
GET /%2e%2e%2f%2e%2e%2fetc%2fpasswd
```

### Extension Whitelisting

Restrict file types to prevent serving sensitive files:

```python
static_handler = StaticFileHandler(
    base_dir='./public',
    allowed_extensions={
        '.html', '.css', '.js',  # Web files
        '.png', '.jpg', '.svg'    # Images
    }
)

# These will return 403 Forbidden:
GET /config.ini
GET /.env
GET /passwords.txt
```

## Testing

Run the example server:

```bash
cd test/restful
python static_files.py
```

Visit `http://localhost:2022` to see the demo page.

## HTTP Methods

- ✅ **GET** - Retrieve file
- ✅ **HEAD** - Get headers only
- ❌ **POST/PUT/DELETE** - Not allowed (405 Method Not Allowed)

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| `200 OK` | Success | File served successfully |
| `403 Forbidden` | Access denied | Path traversal, disallowed extension, directory listing disabled |
| `404 Not Found` | Not found | File doesn't exist, no index file |
| `405 Method Not Allowed` | Method not allowed | POST/PUT/DELETE requests |

## MIME Types

Automatically detected based on file extension:

| Extension | MIME Type |
|-----------|-----------|
| `.html` | `text/html` |
| `.css` | `text/css` |
| `.js` | `application/javascript` |
| `.json` | `application/json` |
| `.png` | `image/png` |
| `.jpg` | `image/jpeg` |
| `.svg` | `image/svg+xml` |
| `.pdf` | `application/pdf` |
| (unknown) | `application/octet-stream` |

## Best Practices

### 1. Use Absolute Paths

```python
import os

base_dir = os.path.abspath('./public')
static_handler = StaticFileHandler(base_dir=base_dir)
```

### 2. Restrict Extensions

Always use `allowed_extensions` in production:

```python
static_handler = StaticFileHandler(
    base_dir='./public',
    allowed_extensions={
        # Only allow safe file types
        '.html', '.css', '.js', '.json',
        '.png', '.jpg', '.svg', '.woff'
    }
)
```

### 3. Disable Directory Listing

```python
static_handler = StaticFileHandler(
    base_dir='./public',
    enable_index=False  # Don't serve directory indexes
)
```

### 4. Use URL Prefixes

Organize your routes with prefixes:

```python
@app.restful_handler("/assets/*")
async def assets(context):
    await asset_handler.handle(context)

@app.restful_handler("/media/*")
async def media(context):
    await media_handler.handle(context)
```

## Common Patterns

### Serve SPA (Single Page Application)

```python
spa_handler = StaticFileHandler(
    base_dir='./dist',
    allowed_extensions={'.html', '.css', '.js', '.json', '.ico'},
    enable_index=True,
    index_files=['index.html']
)
```

### Serve Documentation

```python
docs_handler = StaticFileHandler(
    base_dir='./docs',
    allowed_extensions={'.html', '.css', '.js', '.pdf'},
    url_prefix='/docs'
)
```

### Serve CDN Assets

```python
cdn_handler = StaticFileHandler(
    base_dir='./cdn',
    allowed_extensions={'.css', '.js', '.woff', '.woff2'},
    enable_index=False,
    url_prefix='/cdn'
)
```

## Troubleshooting

### File Not Found (404)

1. Check that `base_dir` path is correct
2. Verify file exists in the directory
3. Check file permissions
4. Ensure URL path matches file path

### Access Denied (403)

1. Check `allowed_extensions` configuration
2. Verify path is within `base_dir` (no traversal)
3. Check if directory listing is disabled

### Wrong MIME Type

Python's `mimetypes` module handles detection. You can add custom types:

```python
import mimetypes
mimetypes.add_type('application/wasm', '.wasm')
```

## API Reference

### Class: `StaticFileHandler`

#### Methods

##### `__init__(base_dir, allowed_extensions=None, enable_index=True, index_files=None, url_prefix="")`

Initialize handler with configuration.

##### `async handle(context: RESTfulContext) -> None`

Handle incoming request and set appropriate response.

##### `_is_safe_path(requested_path: Path) -> bool`

Check if path is within base directory.

##### `_is_allowed_extension(file_path: Path) -> bool`

Check if file extension is allowed.

##### `_get_mime_type(file_path: Path) -> str`

Get MIME type for file.

## License

Part of BasisCore.Server.Edge framework.
