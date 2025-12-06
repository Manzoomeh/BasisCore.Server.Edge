"""Register Custom Logger HTTP Server Example

Demonstrates how to create a custom JSON logger implementation.
Simple example with one custom logger.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Type, TypeVar

from bclib import edge
from bclib.logger import ILogger
from bclib.options.app_options import AppOptions

T = TypeVar('T')


# Custom Logger Implementation: JSON Logger
class JsonLogger(ILogger[T]):
    """
    JSON Logger Implementation

    Logs messages in JSON format for structured logging.
    Useful for log aggregation and analysis tools.
    """

    def __init__(self, options: AppOptions, generic_type_args: tuple[Type, ...] = None):
        """Initialize JSON logger"""
        logger_config = options.get('logger', {})
        logger_type = generic_type_args[0] if generic_type_args else None
        logger_name = logger_config.get(
            'name', logger_type.__name__ if logger_type else 'JsonLogger')

        # Initialize parent logging.Logger
        super().__init__(logger_name)

        # Configure this logger instance
        level_str = logger_config.get('level', 'INFO')
        file_path = logger_config.get('file_path', 'logs/json.log')

        # Convert string level to logging constant
        level = getattr(logging, level_str.upper(), logging.INFO)
        self.setLevel(level)
        self.handlers.clear()

        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # Custom JSON formatter
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'logger': record.name,
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                if record.exc_info:
                    log_data['exception'] = self.formatException(
                        record.exc_info)
                return json.dumps(log_data)

        # Add file handler with JSON formatter
        handler = logging.FileHandler(file_path)
        handler.setFormatter(JsonFormatter())
        self.addHandler(handler)


# Server configuration
options = {
    "http": "localhost:8080",
    'logger': {
            'level': 'INFO',
            'file_path': 'test/logger/api_json.log'
    }
}

app = edge.from_options(options)

# Register custom JSON logger
app.service_provider.add_singleton(
    ILogger, JsonLogger)


@app.restful_handler("api/process")
async def process_request(
    context: edge.RESTfulContext,
    logger: ILogger[None]
):
    """Process API request - uses custom JsonLogger"""
    action = context.query.get('action', 'default')
    user_id = context.query.get('user_id', 'guest')

    # This logger is JsonLogger - logs to logs/api_json.log in JSON format
    logger.info(f"Processing request: {action} for user {user_id}")
    logger.debug(f"Request details - action: {action}, user: {user_id}")

    return {
        "status": "success",
        "action": action,
        "user_id": user_id,
        "logger_type": "JsonLogger",
        "logged_to": "test/logger/api_json.log (JSON format)"
    }


@app.web_handler("logs/view")
async def view_logs():
    """View JSON logs"""
    try:
        with open('test/logger/api_json.log', 'r') as f:
            lines = f.readlines()
            recent = lines[-20:] if len(lines) > 20 else lines

            # Parse JSON and format nicely
            formatted = []
            for line in recent:
                try:
                    data = json.loads(line.strip())
                    formatted.append(
                        f"<pre>{json.dumps(data, indent=2)}</pre>")
                except:
                    formatted.append(f"<pre>{line}</pre>")

            logs_html = "<hr>".join(formatted)
    except FileNotFoundError:
        logs_html = "No logs yet. Make some requests first!"

    return f"""
    <html>
        <head><title>JSON Logs</title></head>
        <body>
            <h1>API Logs (JSON Format)</h1>
            <p>Last 20 entries from logs/api_json.log</p>
            <hr>
            {logs_html}
            <hr>
            <p><a href="/">Back to Home</a></p>
        </body>
    </html>
    """


@app.web_handler()
async def default_handler():
    """Default handler - home page"""
    return """
    <html>
        <head><title>Custom JSON Logger Example</title></head>
        <body>
            <h1>Custom JSON Logger HTTP Server</h1>
            <p><strong>Demonstrates custom JsonLogger implementation</strong></p>

            <h2>Custom Logger:</h2>
            <ul>
                <li>Type: JsonLogger</li>
                <li>Destination: logs/api_json.log</li>
                <li>Format: JSON (structured logging)</li>
            </ul>

            <h2>Available Endpoints:</h2>
            <ul>
                <li><strong>GET</strong> <a href="/api/process?action=login&user_id=123">/api/process?action=login&user_id=123</a> - Process API request</li>
                <li><strong>GET</strong> <a href="/logs/view">/logs/view</a> - View JSON logs</li>
            </ul>

            <h2>How It Works:</h2>
            <ol>
                <li>Create custom JsonLogger class that extends ILogger[T]</li>
                <li>Implement _create_logger() with JSON formatter</li>
                <li>Create factory function for ServiceProvider</li>
                <li>Register with app.service_provider.add_singleton()</li>
                <li>Inject ILogger['ApiService'] in handler</li>
            </ol>

            <p><strong>Make a request, then <a href="/logs/view">view the logs</a>!</strong></p>
        </body>
    </html>
    """


if __name__ == "__main__":
    print("Starting Custom JSON Logger HTTP Server on http://localhost:8085")
    print("\nCustom Logger:")
    print("  Type: JsonLogger")
    print("  Destination: logs/api_json.log")
    print("  Format: JSON")
    print("\nAvailable endpoints:")
    print("  - GET /api/process?action=login&user_id=123")
    print("  - GET /logs/view")
    print("\nView JSON logs at /logs/view!")

    app.listening()
