"""Custom JsonLogger registered as ILogger."""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Type, TypeVar

from bclib import edge
from bclib.context import RESTfulContext, HttpContext
from bclib.logger import ILogger
from bclib.options.app_options import AppOptions

T = TypeVar("T")
LOG_PATH = Path(__file__).resolve().parent / "api_json.log"


class JsonLogger(ILogger[T]):
    def __init__(self, options: AppOptions, generic_type_args: tuple[Type, ...] = None):
        logger_config = options.get("logger", {}) or {}
        logger_type = generic_type_args[0] if generic_type_args else None
        logger_name = logger_config.get(
            "name", logger_type.__name__ if logger_type else "JsonLogger"
        )
        super().__init__(logger_name)
        level = getattr(logging, str(logger_config.get("level", "INFO")).upper(), logging.INFO)
        self.setLevel(level)
        self.handlers.clear()
        file_path = Path(logger_config.get("file_path", str(LOG_PATH)))
        file_path.parent.mkdir(parents=True, exist_ok=True)

        class JsonFormatter(logging.Formatter):
            def format(self, record):
                payload = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "logger": record.name,
                    "level": record.levelname,
                    "message": record.getMessage(),
                }
                return json.dumps(payload)

        handler = logging.FileHandler(file_path)
        handler.setFormatter(JsonFormatter())
        self.addHandler(handler)


options = {
    "name": "logger-custom",
    "http": "localhost:9151",
    "router": {
        "restful": ["api/*"],
        "web": ["*"],
    },
    "logger": {"level": "INFO", "file_path": str(LOG_PATH)},
}

app = edge.from_options(options)
app.service_provider.add_singleton(ILogger, JsonLogger)


@app.restful_handler("api/process", method="GET")
async def process_request(context: RESTfulContext, logger: ILogger[None]):
    action = context.query.get("action", "default")
    logger.info("Processing request: %s", action)
    return {"status": "success", "action": action, "logger": "JsonLogger"}


@app.web_handler()
async def home(_: HttpContext):
    return "<p>Custom logger — try <a href='/api/process?action=login'>/api/process</a></p>"


if __name__ == "__main__":
    print("Custom logger -> http://localhost:9151/api/process?action=login")
    app.listening()
