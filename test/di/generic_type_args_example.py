"""Generic Service with Type Args Example

Demonstrates how generic_type_args are passed to constructors/factories
when using GenericServiceStrategy.
"""

import logging
from typing import Any, Generic, Optional, TypeVar

from bclib.logger import ILogger
from bclib.options.app_options import AppOptions
from bclib.service_provider import ServiceProvider

T = TypeVar('T')


# Example 1: Logger that uses generic_type_args in constructor
class TypedLogger:
    """Logger that knows its type parameter"""

    def __init__(self, options: AppOptions, generic_type_args: Optional[tuple] = None, **kwargs):
        """
        Constructor receives generic_type_args from GenericServiceStrategy

        Args:
            options: Configuration options
            generic_type_args: Type arguments from generic type (e.g., ("MyApp",) for ILogger["MyApp"])
            **kwargs: Additional parameters
        """
        self.type_name = generic_type_args[0] if generic_type_args else "Unknown"
        self.logger = logging.getLogger(self.type_name)
        self.logger.setLevel(options.log_level if hasattr(
            options, 'log_level') else logging.INFO)

        # Add console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            f'[{self.type_name}] %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def info(self, message: str):
        self.logger.info(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)


def example_typed_logger():
    """Example showing generic_type_args passed to constructor"""

    services = ServiceProvider()

    # Register TypedLogger with factory that receives options
    logger_options = AppOptions()
    logger_options.log_level = logging.DEBUG

    def logger_factory(sp, **kwargs):
        # generic_type_args will be in kwargs when resolved via GenericServiceStrategy
        return TypedLogger(logger_options, **kwargs)

    services.add_singleton(TypedLogger, factory=logger_factory)

    # Define handlers with different type parameters
    def user_service_handler(logger: TypedLogger["UserService"]):
        logger.info("Processing user request")
        return "User service complete"

    def product_service_handler(logger: TypedLogger["ProductService"]):
        logger.info("Processing product request")
        return "Product service complete"

    # Inject and execute
    print("=" * 60)
    params1 = services.inject_dependencies(user_service_handler)
    result1 = user_service_handler(**params1)
    print(f"Result: {result1}\n")

    params2 = services.inject_dependencies(product_service_handler)
    result2 = product_service_handler(**params2)
    print(f"Result: {result2}")
    print("=" * 60)

    print("\n✓ TypedLogger with generic_type_args working!")


# Example 2: Repository with entity type awareness
class TypedRepository(Generic[T]):
    """Repository that knows its entity type"""

    def __init__(self, logger: ILogger, generic_type_args: Optional[tuple] = None, **kwargs):
        """
        Constructor receives generic_type_args to know which entity type it handles

        Args:
            logger: Logger instance
            generic_type_args: Entity type from generic parameter
            **kwargs: Additional parameters
        """
        self.logger = logger
        self.entity_type = generic_type_args[0] if generic_type_args else None
        self.entity_name = self.entity_type.__name__ if self.entity_type and hasattr(
            self.entity_type, '__name__') else "Unknown"
        self._data = {}

    def get_all(self):
        self.logger.info(f"Getting all {self.entity_name} entities")
        return list(self._data.values())

    def get_by_id(self, id: Any):
        self.logger.info(f"Getting {self.entity_name} with id {id}")
        return self._data.get(id)

    def add(self, id: Any, entity: T):
        self.logger.info(f"Adding {self.entity_name} with id {id}")
        self._data[id] = entity


class User:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return f"User(name={self.name})"


class Product:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

    def __repr__(self):
        return f"Product(name={self.name}, price={self.price})"


def example_typed_repository():
    """Example showing repository with entity type awareness"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        type_name = kwargs.get('generic_type_args', ("App",))[0]
        return ConsoleLogger.create_logger(type_name if isinstance(type_name, str) else "App", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)

    # Register repository with factory that passes generic_type_args
    def repository_factory(sp, **kwargs):
        logger = sp.get_service(ILogger)
        return TypedRepository(logger, **kwargs)

    services.add_scoped(TypedRepository, factory=repository_factory)

    # Define handlers with different repository types
    def user_handler(repo: TypedRepository[User], logger: ILogger["UserHandler"]):
        logger.info("User handler started")

        # Add some users
        repo.add(1, User("Alice"))
        repo.add(2, User("Bob"))

        users = repo.get_all()
        logger.info(f"Found {len(users)} users: {users}")
        return users

    def product_handler(repo: TypedRepository[Product], logger: ILogger["ProductHandler"]):
        logger.info("Product handler started")

        # Add some products
        repo.add(1, Product("Laptop", 999.99))
        repo.add(2, Product("Mouse", 29.99))

        products = repo.get_all()
        logger.info(f"Found {len(products)} products: {products}")
        return products

    # Inject and execute
    print("=" * 60)
    params1 = services.inject_dependencies(user_handler)
    users = user_handler(**params1)
    print(f"Users: {users}\n")

    # Create new scope for second handler
    services.clear_scope()

    params2 = services.inject_dependencies(product_handler)
    products = product_handler(**params2)
    print(f"Products: {products}")
    print("=" * 60)

    print("\n✓ TypedRepository with entity type awareness working!")


# Example 3: Cache with value type awareness
class TypedCache(Generic[T]):
    """Cache that knows its value type"""

    def __init__(self, logger: ILogger, generic_type_args: Optional[tuple] = None, **kwargs):
        """
        Constructor receives generic_type_args to know value type

        Args:
            logger: Logger instance
            generic_type_args: Value type from generic parameter
            **kwargs: Additional parameters
        """
        self.logger = logger
        self.value_type = generic_type_args[0] if generic_type_args else None
        self.value_type_name = self.value_type.__name__ if self.value_type and hasattr(
            self.value_type, '__name__') else str(self.value_type)
        self._data = {}

        self.logger.info(
            f"TypedCache initialized for type: {self.value_type_name}")

    def get(self, key: str) -> Optional[T]:
        value = self._data.get(key)
        if value is not None:
            self.logger.debug(f"Cache hit for {self.value_type_name}: {key}")
        else:
            self.logger.debug(f"Cache miss for {self.value_type_name}: {key}")
        return value

    def set(self, key: str, value: T):
        self.logger.debug(
            f"Cache set for {self.value_type_name}: {key} = {value}")
        self._data[key] = value


def example_typed_cache():
    """Example showing cache with value type awareness"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.DEBUG

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        type_args = kwargs.get('generic_type_args')
        type_name = type_args[0] if type_args and isinstance(
            type_args[0], str) else "CacheApp"
        return ConsoleLogger.create_logger(type_name, logger_options)

    services.add_singleton(ILogger, factory=logger_factory)

    # Register cache with factory
    def cache_factory(sp, **kwargs):
        logger = sp.get_service(ILogger, **kwargs)
        return TypedCache(logger, **kwargs)

    services.add_singleton(TypedCache, factory=cache_factory)

    # Handlers with different cache types
    def string_cache_handler(cache: TypedCache[str], logger: ILogger["StringHandler"]):
        logger.info("String cache handler started")
        cache.set("greeting", "Hello, World!")
        cache.set("name", "Alice")

        greeting = cache.get("greeting")
        name = cache.get("name")
        logger.info(f"Retrieved: {greeting}, {name}")
        return f"{greeting} {name}"

    def int_cache_handler(cache: TypedCache[int], logger: ILogger["IntHandler"]):
        logger.info("Int cache handler started")
        cache.set("counter", 42)
        cache.set("total", 100)

        counter = cache.get("counter")
        total = cache.get("total")
        logger.info(f"Retrieved counter={counter}, total={total}")
        return counter + total

    # Inject and execute
    print("=" * 60)
    params1 = services.inject_dependencies(string_cache_handler)
    result1 = string_cache_handler(**params1)
    print(f"String result: {result1}\n")

    params2 = services.inject_dependencies(int_cache_handler)
    result2 = int_cache_handler(**params2)
    print(f"Int result: {result2}")
    print("=" * 60)

    print("\n✓ TypedCache with value type awareness working!")


if __name__ == "__main__":
    print("=" * 60)
    print("Example 1: TypedLogger with generic_type_args")
    print("=" * 60)
    example_typed_logger()
    print("\n")

    print("=" * 60)
    print("Example 2: TypedRepository with entity type awareness")
    print("=" * 60)
    example_typed_repository()
    print("\n")

    print("=" * 60)
    print("Example 3: TypedCache with value type awareness")
    print("=" * 60)
    example_typed_cache()
    print("\n")

    print("=" * 60)
    print("All generic_type_args examples completed!")
    print("=" * 60)
