"""
Pytest configuration and fixtures.

Provides common fixtures for all tests.
"""

import pytest
import logging
import allure
from pathlib import Path

from framework.core.hardware_abstraction import HardwareAbstractionLayer
from framework.core.config_loader import ConfigLoader
from framework.core.test_registry import get_test_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def config_loader():
    """
    Provides ConfigLoader instance for the test session.

    Scope: session (created once per test run)
    """
    loader = ConfigLoader()
    # Load configuration using environment variable
    hw_config = loader.load_hardware_config()
    platform = loader.get_platform_name()

    yield loader


@pytest.fixture(scope="session")
def test_registry():
    """
    Provides TestRegistry instance for the test session.

    Scope: session (created once per test run)
    """
    registry = get_test_registry()

    logger.info(f"Loaded test registry with {len(registry._registry)} tests")
    logger.info(f"Available categories: {registry.list_available_categories()}")
    logger.info(f"Available suites: {registry.list_available_suites()}")

    yield registry


@pytest.fixture(scope="session")
def hardware_config(config_loader):
    """
    Provides loaded hardware configuration.
    
    Scope: session
    """
    config = config_loader.load_hardware_config()
    
    # Attach config to Allure report
    allure.attach(
        f"Platform: {config.platform.name}\n"
        f"Version: {config.platform.version}\n"
        f"Vendor: {config.platform.vendor}\n"
        f"Interfaces: {list(config.interfaces.keys())}",
        name="Hardware Configuration",
        attachment_type=allure.attachment_type.TEXT
    )
    
    return config


@pytest.fixture(scope="function")
def hardware(hardware_config):
    """
    Provides initialized Hardware Abstraction Layer.
    
    Automatically initializes and cleans up hardware interfaces.
    Scope: function (new instance for each test)
    
    Usage in tests:
        def test_can_communication(hardware):
            result = hardware.can.send_message(0x123, [0x01, 0x02])
            assert result.success
    """
    logger.info("Initializing hardware for test")
    
    hal = HardwareAbstractionLayer()
    result = hal.initialize()
    
    if not result.success:
        pytest.fail(f"Hardware initialization failed: {result.error}")
    
    # Attach platform info to test
    allure.attach(
        str(hal.get_platform_info()),
        name="Platform Info",
        attachment_type=allure.attachment_type.JSON
    )
    
    yield hal
    
    # Cleanup after test
    logger.info("Cleaning up hardware after test")
    cleanup_result = hal.cleanup()
    
    if not cleanup_result.success:
        logger.warning(f"Hardware cleanup warning: {cleanup_result.error}")


@pytest.fixture(scope="function")
def can_interface(hardware):
    """
    Provides CAN interface adapter.
    
    Scope: function
    """
    if not hardware.has_interface('can'):
        pytest.skip("CAN interface not available in current configuration")
    
    return hardware.can


@pytest.fixture(scope="function")
def serial_interface(hardware):
    """
    Provides serial interface adapter.
    
    Scope: function
    """
    if not hardware.has_interface('serial'):
        pytest.skip("Serial interface not available in current configuration")
    
    return hardware.serial


@pytest.fixture(scope="function")
def gpio_interface(hardware):
    """
    Provides GPIO interface adapter.

    Scope: function
    """
    if not hardware.has_interface('gpio'):
        pytest.skip("GPIO interface not available in current configuration")

    return hardware.gpio


@pytest.fixture(scope="function")
def cli_interface(hardware):
    """
    Provides CLI interface adapter.

    Scope: function
    """
    if not hardware.has_interface('cli'):
        pytest.skip("CLI interface not available in current configuration")

    return hardware.cli_interface


# Dynamic fixture support for auto-discovered adapters
# This allows any {adapter_name}_interface to work automatically

import sys

def __getattr__(name):
    """
    Dynamically create fixtures for {adapter_name}_interface patterns.

    This module-level __getattr__ creates fixtures on-demand for any
    adapter interface requested.
    """
    if name.endswith('_interface') and name not in ['can_interface', 'serial_interface', 'gpio_interface']:
        adapter_name = name[:-10]  # Remove '_interface' suffix

        @pytest.fixture(scope="function")
        def dynamic_interface_fixture(hardware):
            try:
                # Use auto-discovery to get the adapter
                return getattr(hardware, f"{adapter_name}_interface")
            except RuntimeError as e:
                pytest.skip(f"{adapter_name} interface not available: {e}")

        dynamic_interface_fixture.__name__ = name
        dynamic_interface_fixture.__doc__ = f"""
        Provides {adapter_name} interface adapter (auto-generated).

        This fixture is automatically created for any {adapter_name}_interface
        parameter in test functions.

        Scope: function
        """

        # Add to module globals so it can be found
        globals()[name] = dynamic_interface_fixture
        return dynamic_interface_fixture

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


@pytest.fixture
def test_data_dir():
    """
    Provides path to test data directory.
    """
    return Path(__file__).parent / "test_data"


def pytest_configure(config):
    """
    Pytest configuration hook.
    Called before test collection.
    """
    # Add custom markers (also defined in pytest.ini)
    config.addinivalue_line("markers", "smoke: Critical smoke tests")
    config.addinivalue_line("markers", "can_bus: CAN bus tests")
    config.addinivalue_line("markers", "diagnostics: Diagnostic tests")
    
    # Log test configuration
    logger.info("=" * 70)
    logger.info("Automotive Test Framework - Test Session Starting")
    logger.info("=" * 70)


def pytest_collection_finish(session):
    """
    Called after test collection is complete.
    """
    logger.info(f"Collected {len(session.items)} tests")


def pytest_runtest_setup(item):
    """
    Called before each test runs.
    """
    # Check platform-specific markers
    platform_markers = [mark for mark in item.iter_markers()
                       if mark.name.startswith('platform_')]

    if platform_markers:
        # Get current platform
        from framework.core.config_loader import get_config_loader
        loader = get_config_loader()

        try:
            current_platform = loader.get_platform_name()

            # Check if test should run on this platform
            # Test should run if it has the current platform marker OR all_platforms marker
            should_run = any(
                marker.name == f"platform_{current_platform}" or marker.name == "all_platforms"
                for marker in platform_markers
            )

            if not should_run:
                pytest.skip(f"Test not applicable for platform: {current_platform}")

        except RuntimeError:
            # No platform loaded yet
            pass


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to add test result information to Allure report.
    """
    outcome = yield
    report = outcome.get_result()
    
    # Add failure information to Allure
    if report.when == "call" and report.failed:
        # Get failure details
        if hasattr(report, 'longrepr'):
            allure.attach(
                str(report.longrepr),
                name="Failure Details",
                attachment_type=allure.attachment_type.TEXT
            )


def pytest_configure(config):
    """
    Dynamically register markers from test registry to prevent warnings
    """
    try:
        registry = get_test_registry()

        # Get all unique markers from all tests
        all_markers = set()
        for test_metadata in registry._registry.values():
            test_markers = registry.get_pytest_markers(test_metadata.name)
            all_markers.update(test_markers)

        # Register all discovered markers
        for marker in all_markers:
            config.addinivalue_line(
                "markers",
                f"{marker}: Dynamically registered marker from test registry"
            )

    except Exception as e:
        # Don't break pytest if registry loading fails
        logger.warning(f"Failed to register dynamic markers: {e}")


def pytest_sessionfinish(session, exitstatus):
    """
    Called after test session finishes.
    """
    logger.info("=" * 70)
    logger.info(f"Test Session Finished - Exit Status: {exitstatus}")
    logger.info("=" * 70)
