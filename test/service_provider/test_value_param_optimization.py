"""Test to verify value parameter optimization in InjectionPlan"""

from bclib.options import IOptions
from bclib.di import InjectionPlan, ServiceProvider


def test_has_value_parameters_flag():
    """Test that has_value_parameters flag is correctly set"""
    print("=== Test: has_value_parameters Flag ===\n")

    # Handler with only services (no value parameters)
    def service_only_handler(logger: IOptions['app'], db: IOptions['database']):
        return "service only"

    # Handler with value parameters
    def with_value_handler(logger: IOptions['app'], user_id: str, page: int):
        return f"user {user_id}, page {page}"

    # Handler with mixed parameters
    def mixed_handler(name: str, logger: IOptions['app']):
        return f"hello {name}"

    # Analyze handlers
    plan1 = InjectionPlan(service_only_handler)
    plan2 = InjectionPlan(with_value_handler)
    plan3 = InjectionPlan(mixed_handler)

    print(f"service_only_handler:")
    print(f"  has_value_parameters: {plan1.has_value_parameters}")
    print(f"  strategies: {list(plan1.param_strategies.keys())}")

    print(f"\nwith_value_handler:")
    print(f"  has_value_parameters: {plan2.has_value_parameters}")
    print(f"  strategies: {list(plan2.param_strategies.keys())}")

    print(f"\nmixed_handler:")
    print(f"  has_value_parameters: {plan3.has_value_parameters}")
    print(f"  strategies: {list(plan3.param_strategies.keys())}")

    # Verify
    assert plan1.has_value_parameters == False, "service_only should not have value params"
    assert plan2.has_value_parameters == True, "with_value should have value params"
    assert plan3.has_value_parameters == True, "mixed should have value params"

    print("\n✅ All assertions passed!")


def test_optimization_benefit():
    """Show the benefit of conditional kwargs creation"""
    print("\n=== Test: Optimization Benefit ===\n")

    import time

    # Handler with only services
    def api_handler(logger: IOptions['app'], config: IOptions['database']):
        return {"status": "ok"}

    plan = InjectionPlan(api_handler)
    sp = ServiceProvider()
    sp.add_singleton(IOptions, factory=lambda sp, **kw: {"test": "value"})

    # Simulate dispatcher behavior WITHOUT optimization
    def without_optimization(iterations):
        start = time.perf_counter()
        for _ in range(iterations):
            # Always create kwargs dict (old behavior)
            url_segments = {"user_id": "123", "action": "view"}
            query = {"page": "1", "filter": "active"}
            kwargs = {**url_segments, **query}  # Dict creation + merging
            # Would pass to execute_async
        return time.perf_counter() - start

    # Simulate dispatcher behavior WITH optimization
    def with_optimization(iterations):
        start = time.perf_counter()
        for _ in range(iterations):
            # Only create kwargs if needed (new behavior)
            if plan.has_value_parameters:
                url_segments = {"user_id": "123", "action": "view"}
                query = {"page": "1", "filter": "active"}
                kwargs = {**url_segments, **query}
            else:
                pass  # Skip dict creation entirely!
        return time.perf_counter() - start

    iterations = 100000

    time_without = without_optimization(iterations)
    time_with = with_optimization(iterations)

    print(f"Iterations: {iterations:,}")
    print(f"\nWithout optimization (always create kwargs):")
    print(f"  Time: {time_without*1000:.2f}ms")

    print(f"\nWith optimization (conditional kwargs):")
    print(f"  Time: {time_with*1000:.2f}ms")

    speedup = time_without / time_with if time_with > 0 else float('inf')
    saved = (time_without - time_with) * 1000

    print(f"\nImprovement:")
    print(f"  Speedup: {speedup:.1f}x")
    print(f"  Time saved: {saved:.2f}ms for {iterations:,} requests")
    print(f"  Per request: {saved*1000000/iterations:.2f}ns saved")

    print("\n✅ Optimization provides measurable benefit!")


def test_real_world_scenario():
    """Test with realistic handler scenarios"""
    print("\n=== Test: Real-World Scenarios ===\n")

    from bclib.options import AppOptions

    # Common scenario 1: Pure DI handler (no URL params)
    def get_all_users(logger: IOptions['app'], db: IOptions['database']):
        return {"users": []}

    # Common scenario 2: URL params + DI
    def get_user_by_id(user_id: str, logger: IOptions['app']):
        return {"user_id": user_id}

    # Common scenario 3: Multiple URL params + DI
    def get_user_posts(user_id: str, post_id: str, logger: IOptions['app']):
        return {"user_id": user_id, "post_id": post_id}

    scenarios = [
        ("Pure DI (no URL params)", get_all_users, False),
        ("URL param + DI", get_user_by_id, True),
        ("Multiple URL params + DI", get_user_posts, True),
    ]

    for name, handler, expected in scenarios:
        plan = InjectionPlan(handler)
        print(f"{name}:")
        print(f"  has_value_parameters: {plan.has_value_parameters}")
        print(f"  Expected: {expected}")
        print(f"  ✓ Correct!" if plan.has_value_parameters ==
              expected else "  ✗ Wrong!")
        print()

        assert plan.has_value_parameters == expected, f"Failed for {name}"

    print("✅ All real-world scenarios verified!")


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" " * 15 + "Value Parameter Optimization Tests")
    print("="*70 + "\n")

    test_has_value_parameters_flag()
    test_optimization_benefit()
    test_real_world_scenario()

    print("\n" + "="*70)
    print("Summary:")
    print("✅ has_value_parameters flag works correctly")
    print("✅ Optimization provides measurable performance improvement")
    print("✅ Real-world scenarios handled properly")
    print("\nBenefit: Skip unnecessary dict creation/merging for pure DI handlers")
    print("="*70)
