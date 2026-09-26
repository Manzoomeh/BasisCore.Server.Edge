"""Factory registration — factories receive ServiceProvider (+ kwargs)."""
from bclib import edge
from bclib.context import RESTfulContext


class ILogger:
    def log(self, message: str) -> None:
        ...


class IConfig:
    def get(self, key: str) -> str:
        ...


class IDatabase:
    def connect(self) -> str:
        ...


class ConsoleLogger(ILogger):
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")


class AppConfig(IConfig):
    def __init__(self) -> None:
        self.settings = {
            "db_host": "localhost",
            "db_port": "5432",
            "db_name": "demo",
        }

    def get(self, key: str) -> str:
        return self.settings.get(key, "")


class PostgresDatabase(IDatabase):
    def __init__(self, logger: ILogger, config: IConfig) -> None:
        self.logger = logger
        self.config = config
        self.logger.log("PostgresDatabase created")

    def connect(self) -> str:
        host = self.config.get("db_host")
        port = self.config.get("db_port")
        name = self.config.get("db_name")
        uri = f"postgresql://{host}:{port}/{name}"
        self.logger.log(f"Connecting to: {uri}")
        return uri


app = edge.from_options({
    "name": "di-factory",
    "http": "localhost:9102",
    "router": "restful",
})

sp = app.service_provider
sp.add_singleton(ILogger, factory=lambda sp, **kw: ConsoleLogger())
sp.add_singleton(IConfig, factory=lambda sp, **kw: AppConfig())
sp.add_singleton(
    IDatabase,
    factory=lambda sp, **kw: PostgresDatabase(
        sp.get_service(ILogger),
        sp.get_service(IConfig),
    ),
)


@app.restful_handler("api/db", method="GET")
def db_info(db: IDatabase):
    return {"connection": db.connect(), "ok": True}


if __name__ == "__main__":
    print("DI factory -> http://localhost:9102/api/db")
    app.listening()
