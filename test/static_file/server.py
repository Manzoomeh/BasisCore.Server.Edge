"""
Example: Static File Handler
Serves static files from ./public directory
"""
import sys
from pathlib import Path

from bclib import edge
from bclib.context import RESTfulContext
from bclib.utility import StaticFileHandler

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent

# Create app
app = edge.from_options({
    "server": "localhost:2022",
    "router": "web",
    "log_error": True,
    "log_request": True
})

# Create static file handler
# This will serve files from ./test/restful/public directory
static_handler = StaticFileHandler(
    base_dir=SCRIPT_DIR / 'public',
    allowed_extensions={
        # Web files
        '.html', '.htm', '.css', '.js', '.json',
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp',
        # Fonts
        '.woff', '.woff2', '.ttf', '.eot',
        # Documents
        '.pdf', '.txt', '.xml',
        # Media
        '.mp3', '.mp4', '.webm', '.ogg'
    },
    enable_index=True,
    index_files=['index.html', 'index.htm']
)

app.add_static_handler(static_handler)

# @app.web_action()
# async def serve_static_files(context: RESTfulContext):
#     """
#     Serve static files from public directory

#     Examples:
#         GET http://localhost:2022/index.html
#         GET http://localhost:2022/css/style.css
#         GET http://localhost:2022/images/logo.png
#         GET http://localhost:2022/js/app.js
#     """
#     return await static_handler.handle(context)


# Alternative: Serve files with URL prefix (optional - uncomment if you have an assets folder)
# static_assets = StaticFileHandler(
#     base_dir=SCRIPT_DIR / 'assets',
#     allowed_extensions={'.css', '.js', '.png', '.jpg'},
#     url_prefix='/assets'
# )

# Uncomment this handler if you have an assets folder
# @app.restful_action("/assets/*")
# async def serve_assets(context: RESTfulContext):
#     """
#     Serve assets with /assets prefix
#
#     Examples:
#         GET http://localhost:2022/assets/style.css -> ./assets/style.css
#         GET http://localhost:2022/assets/images/logo.png -> ./assets/images/logo.png
#     """
#     await static_assets.handle(context)


if __name__ == "__main__":
    print("=" * 60)
    print("Static File Server Example")
    print("=" * 60)
    print()
    print("Server URL: http://localhost:2022")
    print()
    print("Setup Instructions:")
    print("  1. Create a 'public' directory in the project root")
    print("  2. Add some files (index.html, css/, js/, images/)")
    print("  3. Start this server")
    print("  4. Visit http://localhost:2022")
    print()
    print("Example Directory Structure:")
    print("  public/")
    print("    ├── index.html")
    print("    ├── css/")
    print("    │   └── style.css")
    print("    ├── js/")
    print("    │   └── app.js")
    print("    └── images/")
    print("        └── logo.png")
    print()
    print("Example URLs:")
    print("  - http://localhost:2022/")
    print("  - http://localhost:2022/index.html")
    print("  - http://localhost:2022/css/style.css")
    print("  - http://localhost:2022/images/logo.png")
    print()
    print("=" * 60)

    app.listening()
