"""
Dynamic Test Decorators

Automatically applies pytest and allure decorators based on test registry configuration.
Keeps test code clean by externalizing all decorator logic.
"""

import pytest
import allure
import functools
import logging
from typing import Callable, Any
from framework.core.test_registry import get_test_registry

logger = logging.getLogger(__name__)


def auto_configure_test(func: Callable) -> Callable:
    """
    Automatically configure test with pytest markers and allure decorators
    based on test registry configuration.

    Usage:
        @auto_configure_test
        def test_can_initialization(can_interface):
            # Clean test code without decorators
            result = can_interface.initialize()
            assert result.success
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # Get test metadata from registry
    registry = get_test_registry()
    test_name = func.__name__
    metadata = registry.get_test_metadata(test_name)

    if metadata is None:
        logger.warning(f"Test {test_name} not found in registry, using defaults")
        return wrapper

    # Apply pytest markers dynamically
    for marker in registry.get_pytest_markers(test_name):
        if hasattr(pytest.mark, marker):
            wrapper = getattr(pytest.mark, marker)(wrapper)
        else:
            # Create custom marker if it doesn't exist
            wrapper = pytest.mark.mark(marker)(wrapper)

    # Apply allure decorators dynamically
    allure_labels = registry.get_allure_labels(test_name)

    # Add allure feature
    if 'feature' in allure_labels:
        wrapper = allure.feature(allure_labels['feature'])(wrapper)

    # Add allure story
    if 'story' in allure_labels:
        wrapper = allure.story(allure_labels['story'])(wrapper)

    # Add allure severity
    if 'severity' in allure_labels:
        severity_func = getattr(allure.severity_level, allure_labels['severity'].upper(), None)
        if severity_func:
            wrapper = allure.severity(severity_func)(wrapper)

    # Add allure tag
    if 'tag' in allure_labels:
        wrapper = allure.tag(allure_labels['tag'])(wrapper)

    # Add test description
    wrapper = allure.description(metadata.description)(wrapper)

    logger.debug(f"Configured test {test_name} with metadata: {metadata}")

    return wrapper


def simple_test(func: Callable) -> Callable:
    """
    Simplified decorator that just adds basic test configuration.
    Use this for tests that don't need complex metadata.

    Usage:
        @simple_test
        def test_basic_functionality():
            assert True
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # Apply basic smoke test marker
    wrapper = pytest.mark.smoke(wrapper)
    wrapper = allure.feature("Basic Tests")(wrapper)

    return wrapper


def platform_specific_test(platforms: list):
    """
    Decorator for platform-specific tests.

    Usage:
        @platform_specific_test(["ecu_platform_a", "ecu_platform_b"])
        def test_hardware_specific_feature():
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Add platform markers
        for platform in platforms:
            wrapper = getattr(pytest.mark, f"platform_{platform}")(wrapper)

        # Skip if current platform not in list
        def should_skip():
            import os
            current_platform = os.getenv('HARDWARE_PLATFORM', 'mock_platform')
            return current_platform not in platforms and "all" not in platforms

        wrapper = pytest.mark.skipif(should_skip(), reason=f"Test requires platforms: {platforms}")(wrapper)

        return wrapper

    return decorator


# Convenience decorators for common test types
smoke_test = lambda func: auto_configure_test(pytest.mark.smoke(func))
regression_test = lambda func: auto_configure_test(pytest.mark.regression(func))
integration_test = lambda func: auto_configure_test(pytest.mark.integration(func))
performance_test = lambda func: auto_configure_test(pytest.mark.performance(func))