"""
Factory with ServiceProvider Example

Demonstrates the new factory signature that receives ServiceProvider.
This allows factories to resolve other services from the DI container.
"""
from bclib import edge


# Interfaces
class ILogger:
    def log(self, message: str): ...


class IConfig:
    def get(self, key: str) -> str: ...


class IDatabase:
    def connect(self) -> str: ...


# Implementations
class ConsoleLogger(ILogger):
    def log(self, message: str):
        print(f"[LOG] {message}")


class AppConfig(IConfig):
    def __init__(self):
        self.settings = {
            "db_host": "localhost",
            "db_port": "5432",
            "db_name": "testdb"
        }
    
    def get(self, key: str) -> str:
        return self.settings.get(key, "")


class PostgresDatabase(IDatabase):
    """Database that depends on Logger and Config"""
    
    def __init__(self, logger: ILogger, config: IConfig):
        self.logger = logger
        self.config = config
        self.logger.log("PostgresDatabase created with dependencies!")
    
    def connect(self) -> str:
        host = self.config.get("db_host")
        port = self.config.get("db_port")
        db_name = self.config.get("db_name")
        connection_string = f"postgresql://{host}:{port}/{db_name}"
        self.logger.log(f"Connecting to: {connection_string}")
        return connection_string


# Setup
options = {
    "server": "localhost:8097",
    "router": "restful",
    "log_errors": True
}

app = edge.from_options(options)

print("=" * 70)
print("Factory with ServiceProvider - New Feature")
print("=" * 70)

# Register services
# OLD WAY (no dependencies in factory):
# app.add_singleton(ILogger, factory=lambda: ConsoleLogger())

# NEW WAY - Factory receives ServiceProvider:
app.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())
app.add_singleton(IConfig, factory=lambda sp: AppConfig())

# Factory resolves dependencies from ServiceProvider:
app.add_singleton(
    IDatabase,
    factory=lambda sp: PostgresDatabase(
        sp.get_service(ILogger),
        sp.get_service(IConfig)
    )
)

print("✓ Services registered with factories")
print()


# Test endpoint
@app.restful_action(app.url("api/test"))
async def test_handler(db: IDatabase):
    """Handler with auto-injected database (which has its own dependencies)"""
    connection = db.connect()
    return {
        "success": True,
        "connection": connection,
        "message": "Database service resolved with all its dependencies!"
    }


print("=" * 70)
print("Key Features:")
print("=" * 70)
print("1. Factory functions now receive ServiceProvider as parameter")
print("2. Factories can resolve other services: sp.get_service(ILogger)")
print("3. Complex dependency graphs possible in factories")
print("4. Works with all lifetimes: singleton, scoped, transient")
print()
print("Example:")
print("  app.add_singleton(")
print("      IDatabase,")
print("      factory=lambda sp: PostgresDatabase(")
print("          sp.get_service(ILogger),")
print("          sp.get_service(IConfig)")
print("      )")
print("  )")
print()
print("=" * 70)
print()
print("Server URL: http://localhost:8097")
print("Test endpoint: GET http://localhost:8097/api/test")
print()
print("=" * 70)
print()

# Start server
app.listening()
