"""Value Strategy with List, Tuple, and Set Example

Demonstrates how ValueStrategy handles list, tuple, and set type parameters
in dependency injection.
"""

import logging
from typing import List, Set, Tuple

from bclib.context import AppOptions
from bclib.logger import ILogger
from bclib.service_provider import ServiceProvider


# Example services
class UserService:
    """Service that works with list of user IDs"""

    def __init__(self, logger: ILogger):
        self.logger = logger

    def get_users(self, user_ids: list) -> dict:
        """Get multiple users by IDs"""
        self.logger.info(f"Fetching users with IDs: {user_ids}")
        return {
            "user_ids": user_ids,
            "count": len(user_ids),
            "users": [{"id": uid, "name": f"User {uid}"} for uid in user_ids]
        }


class CoordinateService:
    """Service that works with tuple coordinates"""

    def __init__(self, logger: ILogger):
        self.logger = logger

    def get_location(self, coordinates: tuple) -> dict:
        """Get location info from coordinates"""
        self.logger.info(f"Processing coordinates: {coordinates}")
        lat, lon = coordinates if len(coordinates) >= 2 else (0, 0)
        return {
            "latitude": lat,
            "longitude": lon,
            "coordinates": coordinates
        }


class TagService:
    """Service that works with list of tags"""

    def __init__(self, logger: ILogger):
        self.logger = logger

    def filter_by_tags(self, tags: List[str]) -> dict:
        """Filter items by tags"""
        self.logger.info(f"Filtering by tags: {tags}")
        return {
            "tags": tags,
            "tag_count": len(tags),
            "matched_items": [f"Item matching {tag}" for tag in tags]
        }


class RangeService:
    """Service that works with tuple range"""

    def __init__(self, logger: ILogger):
        self.logger = logger

    def get_items_in_range(self, range_tuple: Tuple[int, int]) -> dict:
        """Get items in specified range"""
        self.logger.info(f"Getting items in range: {range_tuple}")
        start, end = range_tuple
        return {
            "range": range_tuple,
            "start": start,
            "end": end,
            "items": list(range(start, end + 1))
        }


class CategoryService:
    """Service that works with set of unique categories"""

    def __init__(self, logger: ILogger):
        self.logger = logger

    def get_items_by_categories(self, categories: set) -> dict:
        """Get items from unique categories"""
        self.logger.info(f"Fetching items from categories: {categories}")
        return {
            # Convert to sorted list for display
            "categories": sorted(categories),
            "category_count": len(categories),
            "items": [f"Item from {cat}" for cat in categories]
        }


def example_list_injection():
    """Example showing list parameter injection"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("ListExample", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)
    services.add_transient(UserService)

    # Handler with list parameter
    def get_users_handler(service: UserService, user_ids: list):
        """Handler that receives list of user IDs from URL/query"""
        result = service.get_users(user_ids)
        return result

    # Simulate injection with list parameter
    print("=" * 60)
    print("Example 1: List Parameter Injection")
    print("=" * 60)

    # Test with actual list
    params = services.inject_dependencies(
        get_users_handler, user_ids=[1, 2, 3, 4, 5])
    result = get_users_handler(**params)
    print(f"Result with list: {result}")
    print()

    # Test with tuple (will be converted to list)
    params = services.inject_dependencies(
        get_users_handler, user_ids=(10, 20, 30))
    result = get_users_handler(**params)
    print(f"Result with tuple (converted): {result}")
    print()

    print("✓ List injection working!\n")


def example_tuple_injection():
    """Example showing tuple parameter injection"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("TupleExample", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)
    services.add_transient(CoordinateService)

    # Handler with tuple parameter
    def get_location_handler(service: CoordinateService, coordinates: tuple):
        """Handler that receives coordinates as tuple"""
        result = service.get_location(coordinates)
        return result

    # Simulate injection with tuple parameter
    print("=" * 60)
    print("Example 2: Tuple Parameter Injection")
    print("=" * 60)

    # Test with actual tuple
    params = services.inject_dependencies(
        get_location_handler, coordinates=(40.7128, -74.0060))
    result = get_location_handler(**params)
    print(f"Result with tuple: {result}")
    print()

    # Test with list (will be converted to tuple)
    params = services.inject_dependencies(
        get_location_handler, coordinates=[51.5074, -0.1278])
    result = get_location_handler(**params)
    print(f"Result with list (converted): {result}")
    print()

    print("✓ Tuple injection working!\n")


def example_typed_list_injection():
    """Example showing typed List[T] parameter injection"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("TypedListExample", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)
    services.add_transient(TagService)

    # Handler with typed List[str] parameter
    def filter_handler(service: TagService, tags: List[str]):
        """Handler that receives typed list of strings"""
        result = service.filter_by_tags(tags)
        return result

    # Simulate injection
    print("=" * 60)
    print("Example 3: Typed List[str] Parameter Injection")
    print("=" * 60)

    params = services.inject_dependencies(
        filter_handler, tags=["python", "asyncio", "fastapi"])
    result = filter_handler(**params)
    print(f"Result: {result}")
    print()

    print("✓ Typed list injection working!\n")


def example_typed_tuple_injection():
    """Example showing typed Tuple[T, T] parameter injection"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("TypedTupleExample", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)
    services.add_transient(RangeService)

    # Handler with typed Tuple[int, int] parameter
    def range_handler(service: RangeService, range_tuple: Tuple[int, int]):
        """Handler that receives typed tuple of ints"""
        result = service.get_items_in_range(range_tuple)
        return result

    # Simulate injection
    print("=" * 60)
    print("Example 4: Typed Tuple[int, int] Parameter Injection")
    print("=" * 60)

    params = services.inject_dependencies(range_handler, range_tuple=(1, 10))
    result = range_handler(**params)
    print(f"Result: {result}")
    print()

    # Test with list (converted to tuple)
    params = services.inject_dependencies(range_handler, range_tuple=[20, 25])
    result = range_handler(**params)
    print(f"Result with list input: {result}")
    print()

    print("✓ Typed tuple injection working!\n")


def example_set_injection():
    """Example showing set parameter injection"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("SetExample", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)
    services.add_transient(CategoryService)

    # Handler with set parameter
    def get_categories_handler(service: CategoryService, categories: set):
        """Handler that receives unique categories as set"""
        result = service.get_items_by_categories(categories)
        return result

    # Simulate injection with set parameter
    print("=" * 60)
    print("Example 5: Set Parameter Injection")
    print("=" * 60)

    # Test with actual set
    params = services.inject_dependencies(get_categories_handler, categories={
                                          "electronics", "books", "clothing"})
    result = get_categories_handler(**params)
    print(f"Result with set: {result}")
    print()

    # Test with list (will be converted to set, removing duplicates)
    params = services.inject_dependencies(get_categories_handler, categories=[
                                          "food", "food", "drinks", "snacks", "drinks"])
    result = get_categories_handler(**params)
    print(f"Result with list (converted, duplicates removed): {result}")
    print()

    # Test with tuple (will be converted to set)
    params = services.inject_dependencies(
        get_categories_handler, categories=("sports", "outdoor", "fitness"))
    result = get_categories_handler(**params)
    print(f"Result with tuple (converted): {result}")
    print()

    print("✓ Set injection working!\n")


def example_typed_set_injection():
    """Example showing typed Set[T] parameter injection"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("TypedSetExample", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)
    services.add_transient(CategoryService)

    # Handler with typed Set[str] parameter
    def filter_handler(service: CategoryService, categories: Set[str]):
        """Handler that receives typed set of strings"""
        result = service.get_items_by_categories(categories)
        return result

    # Simulate injection
    print("=" * 60)
    print("Example 6: Typed Set[str] Parameter Injection")
    print("=" * 60)

    params = services.inject_dependencies(filter_handler, categories={
                                          "python", "javascript", "typescript", "python"})
    result = filter_handler(**params)
    print(f"Result (note: duplicates automatically removed): {result}")
    print()

    print("✓ Typed set injection working!\n")


def example_url_segment_list():
    """Example showing how list/tuple could be used with URL segments"""

    services = ServiceProvider()

    # Register logger
    logger_options = AppOptions()
    logger_options.log_level = logging.INFO

    def logger_factory(sp, **kwargs):
        from bclib.logger import ConsoleLogger
        return ConsoleLogger.create_logger("URLExample", logger_options)

    services.add_singleton(ILogger, factory=logger_factory)
    services.add_transient(UserService)

    # Handler that could be used with URL like: /users/bulk?ids=1,2,3,4
    def bulk_users_handler(service: UserService, ids: list):
        """Handler for bulk user retrieval"""
        result = service.get_users(ids)
        return result

    print("=" * 60)
    print("Example 7: URL Segment List Usage")
    print("=" * 60)
    print("URL Pattern: /users/bulk?ids=1,2,3,4")
    print()

    # Simulate URL query parameter parsed as list
    # In real scenario, this would come from URL parsing
    params = services.inject_dependencies(bulk_users_handler, ids=[1, 2, 3, 4])
    result = bulk_users_handler(**params)
    print(f"Result: {result}")
    print()

    print("✓ URL segment list working!\n")


if __name__ == "__main__":
    print("\n")
    example_list_injection()
    example_tuple_injection()
    example_typed_list_injection()
    example_typed_tuple_injection()
    example_set_injection()
    example_typed_set_injection()
    example_url_segment_list()

    print("=" * 60)
    print("All list, tuple, and set injection examples completed!")
    print("=" * 60)
