# Generic Services Singleton/Scoped Caching Fix

## Problem Description

When registering generic services like `IOptions[T]` as singleton or scoped, the DI container was incorrectly caching instances based only on the base type, not considering the generic type arguments.

### Bug Example

```python
sp = ServiceProvider()
sp.add_singleton(IOptions, factory=create_options)

# Both resolve to the SAME instance (BUG!)
opt1 = sp.get_service(IOptions['config1'])  # Creates instance
opt2 = sp.get_service(IOptions['config2'])  # Returns same instance as opt1
```

**Expected**: Different instances for different generic type arguments  
**Actual**: Same instance returned for all generic type arguments

## Root Cause

The singleton and scoped caching logic stored instances using only the descriptor (base type):

```python
# OLD CODE (buggy)
if descriptor.lifetime == ServiceLifetime.SINGLETON:
    if descriptor.instance is not None:
        return descriptor.instance  # ❌ Same instance for all generic args
    instance = self._create_instance(descriptor, **kwargs)
    descriptor.instance = instance  # ❌ Caches without considering generic args
    return instance
```

For `IOptions['config1']` and `IOptions['config2']`, both use the same `IOptions` descriptor, so the cache returns the first created instance.

## Solution

Added separate caching mechanisms that consider generic type arguments:

1. **New cache dictionary** for generic singletons:

   ```python
   self._generic_singleton_instances: Dict[tuple, Any] = {}
   ```

2. **Cache key includes both base type AND generic arguments**:

   ```python
   cache_key = (base_type, ('config1',))  # For IOptions['config1']
   cache_key = (base_type, ('config2',))  # For IOptions['config2']
   ```

3. **Updated singleton logic**:

   ```python
   if descriptor.lifetime == ServiceLifetime.SINGLETON:
       generic_type_args = kwargs.get('generic_type_args')

       if generic_type_args:
           # Create cache key from base type + generic args
           cache_key_args = tuple(
               arg.__forward_arg__ if isinstance(arg, ForwardRef) else str(arg)
               for arg in generic_type_args
           )
           cache_key = (base_type_for_cache, cache_key_args)

           # Check generic singleton cache
           if cache_key in self._generic_singleton_instances:
               return self._generic_singleton_instances[cache_key]

           # Create and cache new instance
           instance = self._create_instance(descriptor, **kwargs)
           if instance is not None:
               self._generic_singleton_instances[cache_key] = instance
           return instance
       else:
           # Non-generic singleton - use descriptor's instance cache
           if descriptor.instance is not None:
               return descriptor.instance
           ...
   ```

4. **Same fix applied to scoped services**:
   - Scoped instances now cached per `(base_type, generic_args)` combination
   - Different scopes maintain separate caches

## Behavior After Fix

### Singleton

```python
sp.add_singleton(IOptions, factory=create_options)

opt1_a = sp.get_service(IOptions['config1'])
opt1_b = sp.get_service(IOptions['config1'])  # Same instance ✅
opt2 = sp.get_service(IOptions['config2'])     # Different instance ✅

assert opt1_a is opt1_b  # ✅ Same key = same instance
assert opt1_a is not opt2  # ✅ Different key = different instance
```

### Scoped

```python
sp.add_scoped(IOptions, factory=create_options)

# Scope 1
opt1_a = sp.get_service(IOptions['config1'])
opt1_b = sp.get_service(IOptions['config1'])  # Same instance in scope ✅
opt2 = sp.get_service(IOptions['config2'])     # Different instance ✅

# Scope 2
sp2 = sp.create_scope()
opt1_c = sp2.get_service(IOptions['config1'])  # New instance in new scope ✅

assert opt1_a is opt1_b      # ✅ Same key, same scope
assert opt1_a is not opt2    # ✅ Different key
assert opt1_a is not opt1_c  # ✅ Different scope
```

### Transient

```python
sp.add_transient(IOptions, factory=create_options)

opt1 = sp.get_service(IOptions['config1'])
opt2 = sp.get_service(IOptions['config1'])  # New instance ✅

assert opt1 is not opt2  # ✅ Always creates new instances
```

## Changes Made

### `bclib/service_provider/service_provider.py`

1. **Added `_generic_singleton_instances` cache** (line ~60):

   ```python
   def __init__(self) -> None:
       self._descriptors: Dict[Type, ServiceDescriptor] = {}
       self._scoped_instances: Dict[Type, Any] = {}
       self._generic_singleton_instances: Dict[tuple, Any] = {}  # NEW
   ```

2. **Updated `get_service()` to track base type** (line ~280):

   - Added `base_type_for_cache` and `generic_args_for_cache` variables
   - Tracks base type for both exact matches and generic type resolution

3. **Enhanced singleton caching logic** (line ~300):

   - Checks if generic type arguments exist
   - Creates tuple cache key from (base_type, generic_args)
   - Converts ForwardRef to string for hashable key
   - Uses `_generic_singleton_instances` for generic singletons
   - Falls back to `descriptor.instance` for non-generic singletons

4. **Enhanced scoped caching logic** (line ~340):
   - Same cache key strategy as singleton
   - Uses `_scoped_instances` with tuple keys for generic services
   - Falls back to type keys for non-generic services

## Test Coverage

Created comprehensive tests to verify the fix:

### `test/options/test_singleton_bug.py`

- Tests singleton registration with factory
- Verifies different instances for different keys
- Verifies same instance for same key (caching)
- Tests transient registration

### `test/options/test_generic_lifetimes.py`

- **Singleton test**: Multiple keys, multiple requests per key
- **Scoped test**: Multiple scopes, multiple keys per scope
- **Transient test**: Always creates new instances

All tests passing ✅

## Backward Compatibility

✅ **Fully backward compatible**

- Non-generic services work exactly as before
- Generic services now work correctly with singleton/scoped lifetimes
- No API changes required
- Existing code continues to work

## Performance Impact

Minimal performance impact:

- **Generic services**: Extra tuple creation and dictionary lookup
- **Non-generic services**: Same performance as before (no changes)
- Cache key creation is fast (tuple of strings/ForwardRefs)

## Related Code

This fix enables proper use of `IOptions[T]` with different lifetimes:

```python
# Now works correctly with singleton!
sp.add_singleton(AppOptions, instance=config)
sp.add_singleton(IOptions, factory=create_options)

class Service1:
    def __init__(self, opts: IOptions['database']):
        self.db_config = opts

class Service2:
    def __init__(self, opts: IOptions['cache']):
        self.cache_config = opts

# Each gets correct config, singleton instances cached per key
```
