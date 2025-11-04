# Scripts Reference

VORTEX includes several utility scripts to help with development, testing, and framework management.

## Core Scripts

### `run_tests.py` - Test Runner

The main test execution script with comprehensive filtering and platform support.

#### Basic Usage
```bash
# Using Execution Profiles (Recommended)
python run_tests.py --exec-profile smoke      # Run smoke tests
python run_tests.py --exec-profile hil        # Run HIL tests
python run_tests.py --exec-profile nightly    # Run nightly tests
python run_tests.py --exec-profile regression # Run regression tests

# List available execution profiles
python run_tests.py --list-profiles

# Traditional Usage (Still Supported)
python run_tests.py --category smoke          # Run all smoke tests
python run_tests.py --priority critical       # Run critical priority tests
python run_tests.py --suite can_bus           # Run specific test suite
python run_tests.py tests/suites/can_bus/test_can.py  # Run specific test file
```

#### Filtering Options
```bash
# Execution Profile Filtering
python run_tests.py --exec-profile smoke --suite can_bus
python run_tests.py --exec-profile regression --priority critical
python run_tests.py --exec-profile hil --platform ecu_platform_a

# Traditional Filtering (AND logic)
python run_tests.py --category smoke --priority critical

# Platform-specific tests
export HARDWARE_PLATFORM=ecu_platform_a
python run_tests.py --exec-profile hil

# Mock platform testing
export HARDWARE_PLATFORM=mock_platform
python run_tests.py --exec-profile smoke
```

#### Execution Options
```bash
# Parallel execution with execution profiles
python run_tests.py --exec-profile smoke -n auto      # Auto-detect CPU cores
python run_tests.py --exec-profile regression -n 4    # Use 4 workers

# Verbose output
python run_tests.py --exec-profile smoke -v
python run_tests.py --exec-profile smoke -vv          # Extra verbose

# Stop on first failure
python run_tests.py --exec-profile smoke -x

# Traditional execution options
python run_tests.py --category smoke -n auto
python run_tests.py --category smoke -l               # Show local variables
```

#### Output Options
```bash
# Custom report location
python run_tests.py --category smoke --html-report custom_report.html

# Disable HTML report
python run_tests.py --category smoke --no-html

# JSON output
python run_tests.py --category smoke --json-report results.json
```

#### Help and Information
```bash
# Show all available options
python run_tests.py --help

# List available execution profiles
python run_tests.py --list-profiles

# List available test suites
python run_tests.py --list-suites

# List available categories and priorities
python run_tests.py --list-filters

# Show configuration info
python run_tests.py --show-config
```

### `scripts/create_adapter.py` - Adapter Generator

One-command adapter generation with comprehensive templates and test creation.

#### Basic Usage
```bash
# Generate minimal adapter
python scripts/create_adapter.py my_device

# Generate adapter with custom device path
python scripts/create_adapter.py ethernet --device /dev/eth0

# Generate adapter with custom methods
python scripts/create_adapter.py cli --methods "execute_command,send_ssh_command"

# Generate adapter with tests
python scripts/create_adapter.py spi --tests
```

#### Advanced Options
```bash
# Full-featured generation
python scripts/create_adapter.py modbus \
    --device /dev/ttyRS485 \
    --methods "read_registers,write_registers,read_coils,write_coils" \
    --tests \
    --priority high \
    --category regression \
    --description "Modbus RTU communication adapter"

# Generate with custom test configuration
python scripts/create_adapter.py can_fd \
    --device /dev/can1 \
    --methods "send_fd_message,receive_fd_message,configure_bitrate" \
    --tests \
    --priority critical \
    --category smoke
```

#### Generator Features
- **Auto Device Path Guessing**: Smart defaults based on adapter name
- **Template Processing**: Comprehensive adapter templates with error handling
- **Test Generation**: Complete test suites with multiple scenarios
- **Configuration Integration**: Automatic test registry updates
- **Mock Support**: Automatic mock adapter generation

#### Generated Files
```
# After running: python scripts/create_adapter.py my_device --tests
framework/adapters/my_device_adapter.py          # Main adapter
tests/suites/my_device_tests/                    # Test directory
tests/suites/my_device_tests/test_my_device_comprehensive.py  # Tests
config/test_registry/suites/my_device_tests.yaml # Updated test suite (split structure)
# OR config/test_registry.yaml                   # Updated registry (legacy structure)
```

## Development Scripts

### `scripts/validate_config.py` - Configuration Validator

Validates YAML configuration files for syntax and consistency.

```bash
# Validate all configurations
python scripts/validate_config.py

# Validate specific config
python scripts/validate_config.py --config config/hardware/my_platform.yaml

# Validate test registry (split or legacy)
python scripts/validate_config.py --test-registry

# Validate execution profiles
python scripts/validate_config.py --execution-profiles

# Check for missing test functions
python scripts/validate_config.py --check-tests
```

### `scripts/list_adapters.py` - Adapter Discovery

Lists all available adapters and their capabilities.

```bash
# List all adapters
python scripts/list_adapters.py

# Show adapter details
python scripts/list_adapters.py --details

# Show only mock adapters
python scripts/list_adapters.py --mock-only

# Export adapter list to JSON
python scripts/list_adapters.py --json adapters.json
```

## Utility Scripts

### `scripts/cleanup_reports.py` - Report Management

Manages test report files and directories.

```bash
# Clean old reports (older than 7 days)
python scripts/cleanup_reports.py

# Clean reports older than specific days
python scripts/cleanup_reports.py --days 3

# Clean all reports
python scripts/cleanup_reports.py --all

# Dry run (show what would be deleted)
python scripts/cleanup_reports.py --dry-run
```

### `scripts/platform_info.py` - Platform Information

Shows information about available platforms and current configuration.

```bash
# Show all available platforms
python scripts/platform_info.py

# Show current platform details
python scripts/platform_info.py --current

# Show platform compatibility matrix
python scripts/platform_info.py --compatibility

# Export platform info to JSON
python scripts/platform_info.py --json platforms.json
```

### `scripts/test_stats.py` - Test Statistics

Analyzes test suites and provides statistics.

```bash
# Show test statistics
python scripts/test_stats.py

# Show detailed breakdown by suite
python scripts/test_stats.py --by-suite

# Show platform coverage
python scripts/test_stats.py --platform-coverage

# Generate test metrics report
python scripts/test_stats.py --report test_metrics.html
```

## Docker Scripts

### `scripts/docker_build.py` - Docker Management

Helper script for Docker operations.

```bash
# Build Docker image
python scripts/docker_build.py

# Build with custom tag
python scripts/docker_build.py --tag my-automotive-tests

# Build for specific platform
python scripts/docker_build.py --platform linux/amd64

# Build and push to registry
python scripts/docker_build.py --push --registry my-registry.com
```

### `scripts/docker_run.py` - Docker Test Execution

Simplified Docker test execution with proper device mounting.

```bash
# Run execution profiles in Docker
python scripts/docker_run.py --exec-profile smoke
python scripts/docker_run.py --exec-profile hil --devices /dev/can0,/dev/ttyUSB0

# Traditional usage
python scripts/docker_run.py --category smoke
python scripts/docker_run.py --category regression --devices /dev/can0,/dev/ttyUSB0

# Run with custom platform
python scripts/docker_run.py --platform my_platform --exec-profile smoke

# Run with environment variables
python scripts/docker_run.py --env VORTEX_LOG_LEVEL=DEBUG --exec-profile smoke
```

## CI/CD Scripts

### `scripts/ci_test.py` - CI/CD Test Runner

Specialized script for CI/CD environments with proper exit codes and reporting.

```bash
# Run CI tests using execution profiles (recommended)
python scripts/ci_test.py --exec-profile smoke
python scripts/ci_test.py --exec-profile regression

# Run multiple execution profiles
python scripts/ci_test.py --exec-profiles smoke,regression

# Traditional usage
python scripts/ci_test.py --categories smoke,regression

# Run with custom timeouts
python scripts/ci_test.py --timeout 300

# Generate JUnit XML for CI systems
python scripts/ci_test.py --junit-xml ci_results.xml
```

### `scripts/setup_ci.py` - CI Environment Setup

Sets up the testing environment for CI/CD systems.

```bash
# Setup basic CI environment
python scripts/setup_ci.py

# Setup with custom configuration
python scripts/setup_ci.py --config ci_config.yaml

# Setup for specific CI system
python scripts/setup_ci.py --ci-system github-actions
python scripts/setup_ci.py --ci-system gitlab-ci
python scripts/setup_ci.py --ci-system jenkins
```

## Custom Script Development

### Script Template

Create custom scripts following the framework patterns:

```python
#!/usr/bin/env python3
"""
Custom script template for VORTEX framework
"""

import argparse
import sys
from pathlib import Path

# Add framework to path
framework_root = Path(__file__).parent.parent
sys.path.insert(0, str(framework_root))

from framework.core.config_loader import ConfigLoader
from framework.core.test_registry import get_test_registry

def main():
    parser = argparse.ArgumentParser(description="Custom VORTEX script")
    parser.add_argument("--config", help="Custom configuration file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Load framework configuration
    config_loader = ConfigLoader()
    test_registry = get_test_registry()

    # Your custom logic here
    print("Custom script executed successfully")

if __name__ == "__main__":
    main()
```

### Integration with Framework

Custom scripts can use framework components:

```python
from framework.core.hardware_abstraction import HardwareAbstractionLayer
from framework.core.types import OperationResult

# Initialize hardware
hal = HardwareAbstractionLayer()
result = hal.initialize()

if result.success:
    # Use hardware interfaces
    can_interface = hal.can_interface
    result = can_interface.initialize()
```

## Script Configuration

### Environment Variables

Scripts respect these environment variables:

```bash
# Platform selection
export HARDWARE_PLATFORM=mock_platform

# Configuration directory
export VORTEX_CONFIG_DIR=/custom/config/path

# Log level
export VORTEX_LOG_LEVEL=DEBUG

# Test timeout
export VORTEX_TEST_TIMEOUT=60

# Parallel workers
export VORTEX_WORKERS=4

# Execution profile selection (set by CLI)
export VORTEX_EXECUTION_PROFILE=smoke
export VORTEX_FILTERED_TESTS=test_can_initialization,test_send_can_message
```

### Configuration Files

Scripts can use configuration files:

```yaml
# scripts/config/script_config.yaml
default_platform: "mock_platform"
test_timeout: 300
parallel_workers: 4
report_formats: ["html", "json"]
docker_image: "automotive-tests:latest"
```

## Best Practices

### Script Development
1. **Error Handling**: Always handle errors gracefully
2. **Help Messages**: Provide comprehensive help text
3. **Validation**: Validate inputs before processing
4. **Logging**: Use consistent logging throughout

### Usage Patterns
1. **Start Simple**: Use basic options first
2. **Test Mock First**: Always test with mock platform
3. **Parallel Execution**: Use parallel options for large test suites
4. **CI Integration**: Use CI-specific scripts for automated testing

### Troubleshooting
1. **Check Platform**: Verify `HARDWARE_PLATFORM` is set correctly
2. **Validate Config**: Use validation scripts to check configuration
3. **Check Permissions**: Ensure proper file and device permissions
4. **Use Verbose**: Add `-v` flags for debugging