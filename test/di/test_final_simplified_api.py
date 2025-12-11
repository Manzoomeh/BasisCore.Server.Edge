"""
Final comprehensive test for simplified service_provider API
Tests that all strategy classes work with **kwargs parameter
"""
from bclib.di import (InjectionPlan, InjectionStrategy,
                                    ServiceProvider, ServiceStrategy,
                                    ValueStrategy)

print("=" * 70)
print("Final Test: Simplified Service Provider API")
print("=" * 70)

# Mock context


class URLSegments:
    def __init__(self):
        self.id = '42'
        self.name = 'Alice'
        self.price = '19.99'


class MockContext:
    def __init__(self):
        self.services = ServiceProvider()
        self.url_segments = URLSegments()
        self.event_loop = None

# Mock services


class ILogger:
    def log(self, msg: str): pass


class ConsoleLogger(ILogger):
    def log(self, msg: str):
        print(f"[LOG] {msg}")


class IDatabase:
    def query(self, sql: str): pass


class PostgresDB(IDatabase):
    def query(self, sql: str):
        return f"Result for: {sql}"


# Setup
context = MockContext()
context.services.add_singleton(ILogger, ConsoleLogger)
context.services.add_scoped(IDatabase, PostgresDB)

# Test 1: ValueStrategy with str
print("\n✓ Test 1: ValueStrategy.resolve(**kwargs) - str type")
strategy1 = ValueStrategy('name', str)
result1 = strategy1.resolve(name='Alice')
assert result1 == 'Alice'
print(f"  - Extracted 'name': {result1}")

# Test 2: ValueStrategy with int conversion
print("\n✓ Test 2: ValueStrategy.resolve(**kwargs) - int type")
strategy2 = ValueStrategy('id', int)
result2 = strategy2.resolve(id='42')
assert result2 == 42
assert isinstance(result2, int)
print(
    f"  - Extracted and converted 'id' to int: {result2} (type: {type(result2).__name__})")

# Test 3: ValueStrategy with float conversion
print("\n✓ Test 3: ValueStrategy.resolve(**kwargs) - float type")
strategy3 = ValueStrategy('price', float)
result3 = strategy3.resolve(price='19.99')
assert result3 == 19.99
assert isinstance(result3, float)
print(
    f"  - Extracted and converted 'price' to float: {result3} (type: {type(result3).__name__})")

# Test 4: ServiceStrategy
print("\n✓ Test 4: ServiceStrategy.resolve(**kwargs)")
strategy4 = ServiceStrategy(ILogger)
strategy5 = ServiceStrategy(IDatabase)
result4 = strategy4.resolve(services=context.services, context=context)
result5 = strategy5.resolve(services=context.services, context=context)
assert isinstance(result4, ConsoleLogger)
assert isinstance(result5, PostgresDB)
print(f"  - Resolved ILogger from services: {type(result4).__name__}")
print(f"  - Resolved IDatabase from services: {type(result5).__name__}")

# Test 5: InjectionPlan with mixed parameters
print("\n✓ Test 5: InjectionPlan - complete integration test")


def complex_handler(
    logger: ILogger,
    db: IDatabase,
    id: int,
    name: str,
    price: float
) -> dict:
    logger.log(f"Processing: {name} (ID: {id}) - Price: ${price}")
    query_result = db.query(f"SELECT * FROM products WHERE id={id}")
    return {
        'id': id,
        'name': name,
        'price': price,
        'query': query_result
    }


plan = InjectionPlan(complex_handler)
print(f"  - Created InjectionPlan: {plan}")
print(f"  - Strategies: {list(plan.param_strategies.keys())}")

# Test inject_parameters
kwargs = plan.inject_parameters(context)
print(f"  - Injected {len(kwargs)} parameters:")
for key, value in kwargs.items():
    print(f"    • {key}: {value} (type: {type(value).__name__})")

# Verify types
assert isinstance(kwargs['logger'], ConsoleLogger)
assert isinstance(kwargs['db'], PostgresDB)
assert isinstance(kwargs['id'], int) and kwargs['id'] == 42
assert isinstance(kwargs['name'], str) and kwargs['name'] == 'Alice'
assert isinstance(kwargs['price'], float) and kwargs['price'] == 19.99

# Call handler
result = complex_handler(**kwargs)
print(f"  - Handler result: {result}")

print("\n" + "=" * 70)
print("All Tests Passed! ✓✓✓")
print("\nAPI Summary:")
print("  • InjectionStrategy.resolve(**kwargs) - flexible kwargs-based interface")
print("  • ValueStrategy.resolve(param_name=...) - extracts value with type conversion")
print("  • ServiceStrategy.resolve(services=..., context=...) - resolves from DI")
print("  • InjectionPlan.inject_parameters(context) - unified context interface")
print("  • InjectionPlan.execute_async(context, *args) - simplified execution")
print("  • url_segments flattened into kwargs for ValueStrategy")
print("  • No dependency on Context type in strategies (loosely coupled)")
print("=" * 70)
