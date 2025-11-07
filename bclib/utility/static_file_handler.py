"""Static File Handler - serves static files based on URL path mapping"""
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Set

from bclib.exception import ForbiddenErr
from bclib.utility.response_types import ResponseTypes

if TYPE_CHECKING:
    from bclib.context import RequestContext


class StaticFileHandler:
    """
    Handler for serving static files based on URL path

    Maps URL segments to file system directories and serves files with
    proper MIME types, security checks, and optional features like
    index files and extension whitelisting.

    Example:
        ```python
        # Create handler for ./public directory
        static_handler = StaticFileHandler(
            base_dir='./public',
            allowed_extensions={'.html', '.css', '.js', '.png', '.jpg'},
            enable_index=True
        )

        @app.restful_action()
        async def serve_static(context: RESTfulContext):
            await static_handler.handle(context)
        ```
    """

    def __init__(
        self,
        base_dir: str,
        allowed_extensions: Optional[Set[str]] = None,
        enable_index: bool = True,
        index_files: Optional[List[str]] = None,
        url_prefix: str = ""
    ):
        """
        Initialize static file handler

        Args:
            base_dir: Root directory for static files (absolute or relative)
            allowed_extensions: Set of allowed file extensions with dot (e.g. {'.html', '.css'})
                              If None, all extensions are allowed
            enable_index: If True, serve index files when directory is requested
            index_files: List of index file names to try (default: ['index.html', 'index.htm'])
            url_prefix: URL prefix to strip before mapping to file path (e.g. '/static')
        """
        self.base_dir = Path(base_dir).resolve()
        self.allowed_extensions = allowed_extensions
        self.enable_index = enable_index
        self.index_files = index_files or ['index.html', 'index.htm']
        self.url_prefix = url_prefix.rstrip('/')

        # Ensure base directory exists
        if not self.base_dir.exists():
            raise ValueError(f"Base directory does not exist: {base_dir}")
        if not self.base_dir.is_dir():
            raise ValueError(f"Base directory is not a directory: {base_dir}")

    def _is_safe_path(self, requested_path: Path) -> bool:
        """
        Check if requested path is safe (prevents path traversal attacks)

        Args:
            requested_path: The resolved path to check

        Returns:
            True if path is within base_dir, False otherwise
        """
        try:
            resolved = requested_path.resolve()
            # Check if resolved path is relative to base_dir
            return resolved.is_relative_to(self.base_dir)
        except (ValueError, OSError):
            return False

    def _is_allowed_extension(self, file_path: Path) -> bool:
        """
        Check if file extension is in allowed list

        Args:
            file_path: Path to check

        Returns:
            True if extension is allowed or no whitelist exists
        """
        if self.allowed_extensions is None:
            return True
        return file_path.suffix.lower() in self.allowed_extensions

    def _get_mime_type(self, file_path: Path) -> str:
        """
        Get MIME type for file based on extension

        Args:
            file_path: Path to file

        Returns:
            MIME type string (defaults to 'application/octet-stream')
        """
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'

    def _normalize_url_path(self, url_path: str) -> str:
        """
        Normalize URL path by removing prefix and cleaning up

        Args:
            url_path: Raw URL path from request

        Returns:
            Normalized path string
        """
        # Remove url_prefix if present
        if self.url_prefix and url_path.startswith(self.url_prefix):
            url_path = url_path[len(self.url_prefix):]

        # Remove leading slash and normalize
        return url_path.lstrip('/')

    def _try_index_files(self, dir_path: Path) -> Optional[Path]:
        """
        Try to find an index file in directory

        Args:
            dir_path: Directory to search

        Returns:
            Path to index file if found, None otherwise
        """
        for index_file in self.index_files:
            index_path = dir_path / index_file
            if index_path.is_file():
                return index_path
        return None

    async def handle(self, context: 'RequestContext') -> None:
        """
        Handle static file request

        Args:
            context: Request context

        Sets appropriate response in context (file, error, etc.)
        """
        # Only allow GET and HEAD methods
        method = context.cms.get('method', 'GET').upper()
        if method not in ['GET', 'HEAD']:
            return None

        # Get URL path from request
        request_data = context.cms.get('request', {})
        url_path = request_data.get('url', '')

        # Normalize the path
        normalized_path = self._normalize_url_path(url_path)

        # Convert URL path to file system path
        file_path = self.base_dir / normalized_path

        # Security check: prevent path traversal
        if not self._is_safe_path(file_path):
            raise ForbiddenErr("Access denied: invalid path")

        # Handle directory requests
        if file_path.is_dir():
            if self.enable_index:
                # Try to find index file
                index_path = self._try_index_files(file_path)
                if index_path:
                    file_path = index_path
                else:
                    return None
            else:
                # Directory listing disabled
                return None

        # Check if file exists
        if not file_path.is_file():
            return None

        # Check if extension is allowed
        if not self._is_allowed_extension(file_path):
            return None

        # Get MIME type
        mime_type = self._get_mime_type(file_path)

        # Set response to serve the file
        context.response_type = ResponseTypes.RENDERED
        context.add_header('Content-Type', mime_type)
        return file_path.read_bytes()

    def __repr__(self) -> str:
        """String representation of handler"""
        return (
            f"StaticFileHandler(base_dir='{self.base_dir}', "
            f"allowed_extensions={len(self.allowed_extensions) if self.allowed_extensions else 'all'}, "
            f"enable_index={self.enable_index})"
        )
