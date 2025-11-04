# Testing Guide

VORTEX provides a configuration-driven testing approach where test metadata is managed externally, keeping test code clean and platform-agnostic.

## Writing Tests

### Basic Test Structure

Tests in VORTEX require only the `@auto_configure_test` decorator:

```python
from framework.core.test_decorators import auto_configure_test

@auto_configure_test
def test_can_initialization(can_interface):
    """Test CAN interface initialization"""
    result = can_interface.initialize()
    assert result.success, f"CAN initialization failed: {result.error}"

    # Verify interface is ready
    assert can_interface.is_ready(), "CAN interface not ready"

    # Check status
    status = can_interface.get_status()
    assert "active" in status.lower(), f"Expected active status, got: {status}"
```

### Test Function Requirements

1. **Decorator**: Must use `@auto_configure_test`
2. **Parameters**: Use `{adapter_name}_interface` for auto-fixtures
3. **Assertions**: Use standard pytest assertions
4. **Documentation**: Include docstring describing test purpose

### Available Interfaces

The framework automatically provides interface fixtures:

```python
@auto_configure_test
def test_multiple_interfaces(can_interface, serial_interface, cli_interface):
    """Test using multiple hardware interfaces"""
    # All interfaces automatically provided and configured
    assert can_interface.initialize().success
    assert serial_interface.initialize().success
    assert cli_interface.initialize().success
```

## Test Configuration

### Adding Test Metadata

Configure test metadata in suite files under `config/test_registry/suites/`:

```yaml
# config/test_registry/suites/my_test_suite.yaml
suite_info:
  name: "my_test_suite"
  description: "My custom test suite"
  default_platforms: ["all"]

tests:
  - name: "test_my_functionality"
    category: "smoke"
    priority: "critical"
    description: "Test my custom functionality"
    platforms: ["all"]
    requirements_hardware: false

  - name: "test_hardware_specific"
    category: "regression"
    priority: "high"
    description: "Test requiring real hardware"
    platforms: ["ecu_platform_a", "ecu_platform_b"]
    requirements_hardware: true
```

### Creating Execution Profiles

Organize tests for different scenarios using execution profiles:

```yaml
# config/test_registry/execution/my_profile.yaml
execution_profile:
  name: "my_profile"
  description: "Custom test execution profile"
  timeout: 300

include:
  # Include entire suite
  - suite: "my_test_suite"

  # Include specific tests with overrides
  - suite: "can_bus"
    tests: ["test_can_initialization"]
    overrides:
      timeout: 60
      platforms: ["mock_platform"]
      priority: "critical"
```

### Test Categories

- **smoke**: Critical tests that must pass (quick validation)
- **regression**: Comprehensive test suite (full functionality)
- **integration**: Cross-component integration tests
- **performance**: Performance and load tests

### Test Priorities

- **critical**: Must-pass tests (blocking)
- **high**: Important tests (should pass)
- **medium**: Standard tests (normal priority)
- **low**: Nice-to-have tests (optional)

## Running Tests

### Using Execution Profiles (Recommended)

```bash
# List available execution profiles
python run_tests.py --list-profiles

# Run predefined execution profiles
python run_tests.py --exec-profile smoke      # Fast smoke tests
python run_tests.py --exec-profile hil        # Hardware-in-the-loop tests
python run_tests.py --exec-profile nightly    # Comprehensive nightly run
python run_tests.py --exec-profile regression # Full regression suite

# Run profile with specific platform
python run_tests.py --exec-profile hil --platform ecu_platform_a

# Filter tests within execution profile
python run_tests.py --exec-profile smoke --suite can_bus
python run_tests.py --exec-profile regression --priority critical
```

### Traditional Test Execution (Still Supported)

```bash
# Run all smoke tests
python run_tests.py --category smoke

# Run specific priority tests
python run_tests.py --priority critical

# Run specific test suite
python run_tests.py --suite can_bus

# Run specific test
python run_tests.py tests/suites/can_bus/test_can.py::test_can_initialization
```

### Platform Selection

```bash
# Run on mock platform (default for CI/CD)
export HARDWARE_PLATFORM=mock_platform
python run_tests.py

# Run on real hardware
export HARDWARE_PLATFORM=ecu_platform_a
python run_tests.py --category smoke
```

### Docker Execution

```bash
# Build container
docker build -t automotive-tests .

# Run smoke tests using execution profile
docker run --rm -v $(pwd)/reports:/app/reports automotive-tests --exec-profile smoke

# Run HIL tests with specific platform
docker run --rm -e HARDWARE_PLATFORM=ecu_platform_a -v $(pwd)/reports:/app/reports automotive-tests --exec-profile hil

# Auto device mapping (recommended)
./auto_test.sh my_platform --exec-profile smoke
./auto_test.sh ecu_platform_a --exec-profile hil

# Traditional usage still supported
docker run --rm -v $(pwd)/reports:/app/reports automotive-tests --category smoke
docker run --rm --device=/dev/can0 --device=/dev/ttyUSB0 -e HARDWARE_PLATFORM=ecu_platform_a -v $(pwd)/reports:/app/reports automotive-tests
```

### Parallel Execution

```bash
# Run execution profile in parallel (pytest-xdist)
python run_tests.py --exec-profile smoke -n auto

# Specify number of workers
python run_tests.py --exec-profile regression -n 4

# Traditional parallel execution
python run_tests.py --category smoke -n auto
python run_tests.py --category regression -n 4
```

## Test Organization

### Directory Structure

```
tests/
├── conftest.py                  # Pytest fixtures and configuration
├── suites/
│   ├── can_bus/                 # CAN bus tests
│   │   ├── test_can.py
│   │   └── test_can_filters.py
│   ├── cli_tests/               # CLI adapter tests
│   │   └── test_cli_comprehensive.py
│   ├── diagnostics/             # UDS/diagnostic tests
│   └── system/                  # System-level tests
└── test_data/                   # Test data files
```

### Suite Organization

Group related tests in suites:

```python
# tests/suites/my_device/test_my_device.py
from framework.core.test_decorators import auto_configure_test

@auto_configure_test
def test_my_device_initialization(my_device_interface):
    """Test device initialization"""
    pass

@auto_configure_test
def test_my_device_communication(my_device_interface):
    """Test device communication"""
    pass

@auto_configure_test
def test_my_device_error_handling(my_device_interface):
    """Test device error handling"""
    pass
```

## Advanced Testing

### Custom Test Data

```python
@auto_configure_test
def test_with_custom_data(can_interface, test_data_dir):
    """Test using custom test data"""
    data_file = test_data_dir / "can_messages.json"
    with open(data_file) as f:
        test_messages = json.load(f)

    for msg in test_messages:
        result = can_interface.send_message(msg['id'], msg['data'])
        assert result.success
```

### Parameterized Tests

```python
import pytest
from framework.core.test_decorators import auto_configure_test

@auto_configure_test
@pytest.mark.parametrize("message_id,data", [
    (0x123, [0x01, 0x02, 0x03]),
    (0x456, [0x04, 0x05, 0x06]),
    (0x789, [0x07, 0x08, 0x09]),
])
def test_can_message_sending(can_interface, message_id, data):
    """Test sending various CAN messages"""
    result = can_interface.send_message(message_id, data)
    assert result.success
```

### Mock Configuration in Tests

```python
@auto_configure_test
def test_with_mock_responses(cli_interface):
    """Test using custom mock responses"""
    # Set custom mock response (only works with mock adapters)
    if hasattr(cli_interface, 'set_mock_response'):
        cli_interface.set_mock_response("show version", "Version 1.2.3")

    result = cli_interface.execute_command("show version")
    assert result.success
    assert "Version 1.2.3" in result.data
```

### Error Testing

```python
@auto_configure_test
def test_error_conditions(serial_interface):
    """Test error handling"""
    # Test operation without initialization
    result = serial_interface.send_data(b"test")
    assert not result.success
    assert "not initialized" in result.error.lower()

    # Test invalid operations
    result = serial_interface.initialize()
    assert result.success

    result = serial_interface.send_data(b"")  # Invalid empty data
    assert not result.success
```

## Test Reports

### HTML Reports

Tests automatically generate HTML reports:

```bash
# Reports generated in reports/report.html
python run_tests.py --category smoke

# View reports
python3 -m http.server 8000 -d reports/
# Open: http://localhost:8000/report.html
```

### Report Contents

- Test results and status
- Execution times
- Error details and stack traces
- Platform and environment information
- Hardware configuration details
- Execution profile information (when used)

### CI/CD Integration

```yaml
# GitHub Actions example with execution profiles
- name: Run Smoke Tests
  run: |
    docker run --rm -e HARDWARE_PLATFORM=mock_platform \
      -v ${{ github.workspace }}/reports:/app/reports \
      automotive-tests --exec-profile smoke

- name: Run Regression Tests
  run: |
    docker run --rm -e HARDWARE_PLATFORM=mock_platform \
      -v ${{ github.workspace }}/reports:/app/reports \
      automotive-tests --exec-profile regression

- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  with:
    name: test-reports
    path: reports/
```

## Best Practices

### Test Design

1. **Single Responsibility**: Each test should test one specific functionality
2. **Clear Assertions**: Use descriptive assertion messages
3. **Cleanup**: Framework handles automatic cleanup via fixtures
4. **Independence**: Tests should not depend on each other

### Mock Testing

1. **Use Mock Platform**: Test logic without hardware dependencies
2. **Custom Responses**: Configure mock responses for specific scenarios
3. **Error Simulation**: Test error conditions with mock adapters

### Hardware Testing

1. **Platform Selection**: Use appropriate hardware platform
2. **Hardware Checks**: Verify hardware availability before testing
3. **Resource Management**: Framework handles initialization/cleanup

### Performance

1. **Execution Profiles**: Use profiles for organized test execution
2. **Parallel Execution**: Use `-n auto` for parallel test execution
3. **Mock for Speed**: Use mock platform for rapid feedback
4. **Selective Testing**: Run specific categories/priorities as needed

## Troubleshooting

### Common Issues

**Test Not Found**:
- Check test function name matches registry entry
- Verify test is in correct suite directory

**Fixture Not Available**:
- Check adapter name matches interface parameter
- Verify adapter is properly auto-discovered
- Ensure hardware platform is configured

**Hardware Issues**:
- Check device permissions and paths
- Verify hardware platform configuration
- Use mock platform for testing framework logic

**Configuration Errors**:
- Validate YAML syntax in suite and execution profile files
- Check test registry entries in `config/test_registry/`
- Verify platform selection
- Ensure execution profile exists: `python run_tests.py --list-profiles`