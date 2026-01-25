"""
Test utilities and helpers for BAML-Langchain integration tests
"""

import time
from contextlib import contextmanager
from baml_client.type_builder import TypeBuilder

@contextmanager
def timer(name: str):
    """Context manager for timing test execution"""
    start = time.time()
    yield
    end = time.time()
    print(f"⏱️  {name} took {end - start:.3f} seconds")

def create_test_typebuilder() -> TypeBuilder:
    """Create a TypeBuilder with common test properties"""
    tb = TypeBuilder()
    tb.DynamicSchema.add_property("test_id", tb.string())
    tb.DynamicSchema.add_property("timestamp", tb.int())
    return tb

def assert_has_property(tb: TypeBuilder, property_name: str):
    """Assert that TypeBuilder has the specified property"""
    assert hasattr(tb.DynamicSchema, property_name), \
        f"TypeBuilder missing property: {property_name}"

def get_sample_tool_combinations():
    """Get various tool combinations for testing"""
    from test.fixtures.sample_tools import (
        CalculatorAdd, CalculatorSubtract, get_weather, search_web
    )

    return {
        "single_pydantic": [CalculatorAdd],
        "single_langchain": [get_weather],
        "mixed_small": [CalculatorAdd, get_weather],
        "mixed_large": [CalculatorAdd, CalculatorSubtract, get_weather, search_web]
    }

def run_performance_test(test_func, iterations: int = 10):
    """Run a performance test with multiple iterations"""
    times = []

    for i in range(iterations):
        start = time.time()
        test_func()
        end = time.time()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    print(f"📊 Performance Results ({iterations} iterations):")
    print(f"   Average: {avg_time:.4f}s")
    print(f"   Minimum: {min_time:.4f}s")
    print(f"   Maximum: {max_time:.4f}s")

    return {
        "average": avg_time,
        "minimum": min_time,
        "maximum": max_time,
        "all_times": times
    }