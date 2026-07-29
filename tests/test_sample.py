import importlib

import pytest


def test_sample():
    """Sample test to verify pytest works"""
    assert True


@pytest.mark.parametrize("module", [
    "dependency_health",
    "performance_benchmark",
    "pipeline_dashboard",
    "smart_test_selector",
])
def test_imports(module):
    """Test that all modules can be imported"""
    mod = importlib.import_module(module)
    assert mod is not None, f"{module} imported but is None"
