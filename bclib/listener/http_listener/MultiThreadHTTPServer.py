from socketserver import ThreadingMixIn
from http.server import HTTPServer


class MultiThreadHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
