# Factory Signature Update - Complete

## Summary

Factory functions in the dependency injection system now receive `ServiceProvider` as a parameter, enabling them to resolve other services from the DI container.

## Changes Made

### 1. Updated ServiceProvider (`bclib/service_provider/service_provider.py`)

- Changed factory signature from `Callable[[], T]` to `Callable[['ServiceProvider'], T]`
- Updated methods: `add_singleton()`, `add_scoped()`, `add_transient()`
- Modified `_create_instance()` to pass `self` to factory: `factory(self)`

### 2. Updated ServiceDescriptor (`bclib/service_provider/service_descriptor.py`)

- Added `TYPE_CHECKING` import for forward reference
- Updated factory parameter: `Callable[['ServiceProvider'], Any]`
- Updated docstring to mention ServiceProvider parameter

### 3. Updated Dispatcher (`bclib/dispatcher/dispatcher.py`)

- Changed factory signature in: `add_singleton()`, `add_scoped()`, `add_transient()`
- Updated docstring examples

## API Changes

### Old API (Before)

```python
services.add_singleton(ILogger, factory=lambda: ConsoleLogger())
```

### New API (Now)

```python
# Simple factory
services.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())

# Factory with dependencies
services.add_singleton(
    IDatabase,
    factory=lambda sp: PostgresDatabase(
        sp.get_service(ILogger),
        sp.get_service(IConfig)
    )
)
```

## Benefits

1. **Dependency Resolution**: Factories can now resolve other services
2. **Flexible Construction**: Complex initialization logic with dependencies
3. **All Lifetimes**: Works with singleton, scoped, and transient
4. **Standard Pattern**: Aligns with DI frameworks like ASP.NET Core

## Examples

### Basic Factory

```python
services.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())
```

### Factory with Dependencies

```python
services.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())
services.add_singleton(IConfig, factory=lambda sp: AppConfig())

services.add_singleton(
    IDatabase,
    factory=lambda sp: PostgresDatabase(
        logger=sp.get_service(ILogger),
        config=sp.get_service(IConfig)
    )
)
```

### Scoped Factory

```python
services.add_scoped(
    IUserContext,
    factory=lambda sp: UserContext(
        sp.get_service(ILogger),
        sp.get_service(IDatabase)
    )
)
```

### Transient Factory

```python
services.add_transient(
    ICommandHandler,
    factory=lambda sp: CommandHandler(sp.get_service(ILogger))
)
```

## Testing

All tests pass:

- ✅ Existing tests (no breaking changes for non-factory registrations)
- ✅ New unit tests for factory with ServiceProvider
- ✅ Tests for all lifetimes (singleton, scoped, transient)

## Files Modified

1. `bclib/service_provider/service_provider.py`
2. `bclib/service_provider/service_descriptor.py`
3. `bclib/dispatcher/dispatcher.py`

## New Test Files

1. `test/di/test_factory_with_sp.py` - Unit tests for new feature
2. `test/di/factory_with_dependencies.py` - Example demonstrating feature

## Migration Guide

Existing code without factories continues to work:

```python
# This still works
app.add_singleton(ILogger, ConsoleLogger)
app.add_singleton(ILogger, implementation=ConsoleLogger)
```

If using factories, add `sp` parameter:

```python
# Before
app.add_singleton(ILogger, factory=lambda: ConsoleLogger())

# After
app.add_singleton(ILogger, factory=lambda sp: ConsoleLogger())
```

If factory needs dependencies, use `sp.get_service()`:

```python
app.add_singleton(
    IDatabase,
    factory=lambda sp: PostgresDatabase(sp.get_service(ILogger))
)
```
