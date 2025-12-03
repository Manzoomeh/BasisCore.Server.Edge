"""Generic Service Injection Example

Demonstrates how the GenericServiceStrategy automatically handles
parameterized generic types like ILogger[T], Repository[User], etc.
"""

import logging
from typing import Generic, TypeVar

from bclib.app_options import AppOptions
from bclib.logger import ILogger
from bclib.service_provider import ServiceProvider

T = TypeVar('T')


# Example 1: Using ILogger with generic type parameter
def example_logger_injection():
    """Example of injecting ILogger[T] with different type parameters"""

    services = ServiceProvider()

    # Register logger factory
    logger_options = AppOptions()
    # logger_options.log_level = logging.DEBUG

    def logger_factory(sp):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("GenericApp", logger_options)

    # Register as ILogger (base type)
    services.add_singleton(ILogger, factory=logger_factory)

    # Define handlers with different generic type parameters
    def handler1(logger: ILogger["Service1"]):
        """Handler with ILogger[Service1]"""
        logger.info("Handler1 executing with generic logger")
        return "Handler1 complete"

    def handler2(logger: ILogger["Service2"]):
        """Handler with ILogger[Service2]"""
        logger.debug("Handler2 executing with generic logger")
        return "Handler2 complete"

    # Inject and execute
    params1 = services.inject_dependencies(handler1)
    result1 = handler1(**params1)
    print(f"Result 1: {result1}")

    params2 = services.inject_dependencies(handler2)
    result2 = handler2(**params2)
    print(f"Result 2: {result2}")

    print("\n✓ Generic logger injection working!")


# Example 2: Custom generic service
class Repository(Generic[T]):
    """Generic repository pattern"""

    def __init__(self, logger: ILogger):
        self.logger = logger
        self.entity_type = T

    def get_all(self):
        self.logger.info(f"Getting all entities of type {self.entity_type}")
        return []

    def get_by_id(self, id: int):
        self.logger.debug(f"Getting entity {id} of type {self.entity_type}")
        return None


class User:
    """Example entity"""
    pass


class Product:
    """Example entity"""
    pass


def example_repository_injection():
    """Example of injecting Repository[T] with different entity types"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("RepositoryApp", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)

    # Register repository as base generic type
    services.add_scoped(Repository, implementation=Repository)

    # Define handlers with different repository types
    def user_handler(repo: Repository[User], logger: ILogger["UserService"]):
        """Handler with Repository[User]"""
        logger.info("User handler executing")
        users = repo.get_all()
        return f"Found {len(users)} users"

    def product_handler(repo: Repository[Product], logger: ILogger["ProductService"]):
        """Handler with Repository[Product]"""
        logger.info("Product handler executing")
        products = repo.get_all()
        return f"Found {len(products)} products"

    # Inject and execute
    params1 = services.inject_dependencies(user_handler)
    result1 = user_handler(**params1)
    print(f"User Handler: {result1}")

    params2 = services.inject_dependencies(product_handler)
    result2 = product_handler(**params2)
    print(f"Product Handler: {result2}")

    print("\n✓ Generic repository injection working!")


# Example 3: Multiple generic parameters
class Cache(Generic[T]):
    """Generic cache"""

    def __init__(self, logger: ILogger["Cache"]):
        self.logger = logger
        self._data = {}

    def get(self, key: str):
        self.logger.debug(f"Cache get: {key}")
        return self._data.get(key)

    def set(self, key: str, value: T):
        self.logger.debug(f"Cache set: {key} = {value}")
        self._data[key] = value


def example_cache_injection():
    """Example of injecting Cache[T] with different value types"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.DEBUG

    def logger_factory(sp):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("CacheApp", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)
    services.add_singleton(Cache, implementation=Cache)

    # Handlers with different cache types
    def string_cache_handler(cache: Cache[str], logger: ILogger["StringService"]):
        """Handler with Cache[str]"""
        logger.info("Using string cache")
        cache.set("key1", "value1")
        return cache.get("key1")

    def int_cache_handler(cache: Cache[int], logger: ILogger["IntService"]):
        """Handler with Cache[int]"""
        logger.info("Using int cache")
        cache.set("counter", 42)
        return cache.get("counter")

    # Inject and execute
    params1 = services.inject_dependencies(string_cache_handler)
    result1 = string_cache_handler(**params1)
    print(f"String Cache Result: {result1}")

    params2 = services.inject_dependencies(int_cache_handler)
    result2 = int_cache_handler(**params2)
    print(f"Int Cache Result: {result2}")

    print("\n✓ Generic cache injection working!")


# Example 4: Real-world usage with edge handlers
def example_edge_handler_with_generics():
    """Example showing how generics work with edge handlers"""

    from bclib import edge

    # Setup edge with DI
    options = {"http": "localhost:8080"}
    app = edge.from_options(options)

    # Configure DI container
    services = ServiceProvider()

    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("EdgeApp", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)

    # Define handler with generic logger
    @app.restful_handler("users/{id}")
    async def get_user(
        id: int,
        logger: ILogger["UserAPI"]
    ):
        """
        Handler automatically gets:
        - id: from URL segment (ValueStrategy)
        - logger: from DI container (GenericServiceStrategy)
        """
        logger.info(f"Getting user {id}")
        return {
            "id": id,
            "name": f"User {id}"
        }

    print("✓ Edge handler with generic logger configured!")
    print(f"  Handler: {get_user.__name__}")
    print(f"  URL: /users/{{id}}")
    print(f"  Injected: id (int), logger (ILogger['UserAPI'])")


if __name__ == "__main__":
    print("=" * 60)
    print("Example 1: Logger Generic Injection")
    print("=" * 60)
    example_logger_injection()
    print()

    print("=" * 60)
    print("Example 2: Repository Generic Injection")
    print("=" * 60)
    example_repository_injection()
    print()

    print("=" * 60)
    print("Example 3: Cache Generic Injection")
    print("=" * 60)
    example_cache_injection()
    print()

    print("=" * 60)
    print("Example 4: Edge Handler with Generics")
    print("=" * 60)
    example_edge_handler_with_generics()
    print()

    print("=" * 60)
    print("All generic injection examples completed!")
    print("=" * 60)
