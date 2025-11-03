# User Integration Guide

This guide shows how users can integrate their own hardware configurations, test cases, and adapters into the VORTEX framework. We follow a template/example approach where users copy and modify provided examples.

## Integration Overview

VORTEX supports user integration through:

1. **Custom Hardware Platforms** - Define your specific hardware setup
2. **Custom Test Suites** - Add your own test cases and scenarios
3. **Custom Adapters** - Create adapters for proprietary devices
4. **Custom Configurations** - Tailor framework behavior to your needs

## Setting Up Your Custom Configuration

### 1. Create Your Hardware Platform

Copy an existing platform configuration and modify for your hardware:

```bash
# Copy mock platform as a starting point
cp config/hardware/mock_platform.yaml config/hardware/my_company_platform.yaml
```

Edit the configuration for your hardware:

```yaml
# config/hardware/my_company_platform.yaml
platform:
  name: "My Company ECU Platform"
  version: "1.0"
  vendor: "My Company"
  description: "Company-specific ECU testing platform"

interfaces:
  # Define your specific hardware interfaces
  company_ecu:
    type: "custom"
    device_path: "/dev/ttyACM0"
    baudrate: 921600
    protocol: "proprietary"

  company_can:
    type: "socketcan"
    channel: "can1"
    bitrate: 1000000
    fd_enabled: true

  company_diagnostic:
    type: "uds"
    transport: "doip"
    ip_address: "192.168.1.50"
    port: 13400

# Add your company-specific test parameters
test_parameters:
  company_timeout: 15.0
  max_retry_count: 5
  diagnostic_delay: 2.0

# Custom settings specific to your platform
company_settings:
  test_mode: "development"
  debug_level: "verbose"
  custom_protocols: ["proprietary_v1", "proprietary_v2"]
```

### 2. Add Your Test Suites

Create test suite configuration in the test registry:

```yaml
# Add to config/test_registry.yaml
test_suites:
  company_ecu_tests:
    description: "Company ECU specific tests"
    platforms: ["my_company_platform", "mock_platform"]
    tests:
      - name: "test_company_ecu_initialization"
        category: "smoke"
        priority: "critical"
        description: "Test company ECU initialization sequence"
        platforms: ["my_company_platform"]
        requirements_hardware: true

      - name: "test_company_protocol_communication"
        category: "regression"
        priority: "high"
        description: "Test proprietary protocol communication"
        platforms: ["my_company_platform"]
        requirements_hardware: true

  company_integration_tests:
    description: "Company system integration tests"
    platforms: ["my_company_platform"]
    tests:
      - name: "test_end_to_end_workflow"
        category: "integration"
        priority: "critical"
        description: "Test complete company workflow"
        platforms: ["my_company_platform"]
```

### 3. Create Your Test Cases

Create test files following the framework structure:

```bash
# Create your test directory
mkdir -p tests/suites/company_ecu_tests
```

Write your test cases:

```python
# tests/suites/company_ecu_tests/test_company_ecu.py
from framework.core.test_decorators import auto_configure_test

@auto_configure_test
def test_company_ecu_initialization(company_ecu_interface):
    """Test company ECU initialization sequence"""
    # Custom initialization sequence for your ECU
    result = company_ecu_interface.initialize()
    assert result.success, f"ECU initialization failed: {result.error}"

    # Company-specific validation
    version = company_ecu_interface.get_firmware_version()
    assert version.startswith("COMP_"), f"Invalid firmware version: {version}"

    # Test company-specific features
    result = company_ecu_interface.enter_test_mode()
    assert result.success, "Failed to enter test mode"

@auto_configure_test
def test_company_protocol_communication(company_ecu_interface):
    """Test proprietary protocol communication"""
    # Initialize ECU
    result = company_ecu_interface.initialize()
    assert result.success

    # Test company-specific protocol
    test_command = {
        "cmd": "GET_STATUS",
        "params": {"subsystem": "engine"}
    }

    result = company_ecu_interface.send_proprietary_command(test_command)
    assert result.success
    assert result.data["status"] == "OK"
```

## Creating Custom Adapters

### 1. Generate Adapter Template

Use the framework generator to create your custom adapter:

```bash
# Generate adapter for your proprietary device
python scripts/create_adapter.py company_ecu \
    --device /dev/ttyACM0 \
    --methods "send_proprietary_command,get_firmware_version,enter_test_mode" \
    --tests \
    --priority critical
```

### 2. Customize Generated Adapter

Edit the generated adapter to implement your specific protocol:

```python
# framework/adapters/company_ecu_adapter.py
import serial
import json
from typing import Dict, Any
from framework.core.types import OperationResult

class CompanyEcuAdapter:
    def __init__(self, config):
        self.config = config
        self.device_path = config.get('device_path', '/dev/ttyACM0')
        self.baudrate = config.get('baudrate', 921600)
        self.protocol = config.get('protocol', 'proprietary')
        self._connection = None
        self._is_initialized = False

    def initialize(self) -> OperationResult:
        """Initialize connection to company ECU"""
        try:
            self._connection = serial.Serial(
                port=self.device_path,
                baudrate=self.baudrate,
                timeout=5.0
            )

            # Company-specific initialization sequence
            init_cmd = {"cmd": "INIT", "version": "1.0"}
            response = self._send_command(init_cmd)

            if response.get("status") != "READY":
                return OperationResult(
                    success=False,
                    error=f"ECU not ready: {response}"
                )

            self._is_initialized = True
            return OperationResult(
                success=True,
                log="Company ECU initialized successfully"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to initialize ECU: {str(e)}"
            )

    def send_proprietary_command(self, command: Dict[str, Any]) -> OperationResult:
        """Send proprietary protocol command"""
        if not self.is_ready():
            return OperationResult(success=False, error="ECU not initialized")

        try:
            response = self._send_command(command)
            return OperationResult(
                success=True,
                data=response,
                log=f"Command executed: {command['cmd']}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Command failed: {str(e)}"
            )

    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to send command and receive response"""
        # Implement your company's protocol here
        cmd_json = json.dumps(command) + '\n'
        self._connection.write(cmd_json.encode())

        response_line = self._connection.readline().decode().strip()
        return json.loads(response_line)

# Mock adapter for testing
class MockCompanyEcuAdapter(CompanyEcuAdapter):
    def __init__(self, config):
        super().__init__(config)
        self._mock_responses = {
            "INIT": {"status": "READY", "version": "COMP_1.2.3"},
            "GET_STATUS": {"status": "OK", "subsystem": "engine"},
        }

    def initialize(self) -> OperationResult:
        self._is_initialized = True
        return OperationResult(success=True, log="Mock ECU initialized")

    def _send_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        cmd_name = command.get("cmd", "UNKNOWN")
        return self._mock_responses.get(cmd_name, {"status": "ERROR", "msg": "Unknown command"})
```

## Configuration Management

### Environment-Based Configuration

Use environment variables to switch between configurations:

```bash
# For development
export HARDWARE_PLATFORM=my_company_platform
export VORTEX_LOG_LEVEL=DEBUG
export COMPANY_TEST_MODE=development

# For production testing
export HARDWARE_PLATFORM=my_company_platform
export VORTEX_LOG_LEVEL=INFO
export COMPANY_TEST_MODE=production

# For CI/CD (mock)
export HARDWARE_PLATFORM=mock_platform
export VORTEX_LOG_LEVEL=INFO
```

### Custom Configuration Loading

Extend configuration loading for company-specific settings:

```python
# Custom configuration loader (optional)
from framework.core.config_loader import ConfigLoader
import os

class CompanyConfigLoader(ConfigLoader):
    def load_company_settings(self):
        """Load company-specific settings"""
        settings = {
            'test_mode': os.getenv('COMPANY_TEST_MODE', 'development'),
            'debug_enabled': os.getenv('COMPANY_DEBUG', 'false').lower() == 'true',
            'custom_protocols': os.getenv('COMPANY_PROTOCOLS', '').split(',')
        }
        return settings
```

## Testing Your Integration

### 1. Test Mock Platform First

Always test with mock platform before using real hardware:

```bash
# Test with mock platform
export HARDWARE_PLATFORM=mock_platform
python run_tests.py --suite company_ecu_tests
```

### 2. Validate Hardware Platform

Test individual components before full integration:

```bash
# Test specific adapter
export HARDWARE_PLATFORM=my_company_platform
python run_tests.py tests/suites/company_ecu_tests/test_company_ecu.py::test_company_ecu_initialization
```

### 3. Integration Testing

Run full integration tests:

```bash
# Run all company tests
export HARDWARE_PLATFORM=my_company_platform
python run_tests.py --suite company_ecu_tests --suite company_integration_tests
```

## Docker Integration

### Custom Docker Configuration

Create a company-specific Dockerfile if needed:

```dockerfile
# Dockerfile.company
FROM automotive-tests:latest

# Add company-specific dependencies
RUN apt-get update && apt-get install -y \
    company-proprietary-tools \
    custom-drivers

# Copy company configurations
COPY config/hardware/my_company_platform.yaml /app/config/hardware/
COPY tests/suites/company_* /app/tests/suites/

# Set default platform
ENV HARDWARE_PLATFORM=my_company_platform
```

Build and run:

```bash
docker build -f Dockerfile.company -t company-automotive-tests .
docker run --rm \
    --device=/dev/ttyACM0 \
    -v $(pwd)/reports:/app/reports \
    company-automotive-tests --suite company_ecu_tests
```

## Best Practices

### Configuration Organization

1. **Namespace Your Configs**: Use company prefix for hardware platforms
2. **Document Dependencies**: List required hardware and software
3. **Version Control**: Keep configurations in version control
4. **Environment Separation**: Use different configs for dev/test/prod

### Test Organization

1. **Suite Grouping**: Group related tests in logical suites
2. **Clear Naming**: Use descriptive test and suite names
3. **Documentation**: Document test purpose and requirements
4. **Mock Support**: Always provide mock equivalents

### Adapter Development

1. **Error Handling**: Implement comprehensive error handling
2. **Configuration**: Make adapters configurable via YAML
3. **Testing**: Provide both real and mock implementations
4. **Documentation**: Document protocol and usage

### Maintenance

1. **Updates**: Keep up with framework updates
2. **Testing**: Test integrations with each framework version
3. **Documentation**: Maintain integration documentation
4. **Sharing**: Consider contributing generic adapters back

## Example: Complete Integration

Here's a complete example showing all integration components:

### Hardware Platform
```yaml
# config/hardware/acme_test_bench.yaml
platform:
  name: "ACME Test Bench"
  vendor: "ACME Corp"

interfaces:
  acme_controller:
    type: "custom"
    device_path: "/dev/ttyUSB0"
    protocol: "acme_v2"
```

### Test Registry
```yaml
# In config/test_registry.yaml
test_suites:
  acme_controller_tests:
    description: "ACME controller tests"
    platforms: ["acme_test_bench", "mock_platform"]
    tests:
      - name: "test_acme_initialization"
        category: "smoke"
        priority: "critical"
```

### Test Implementation
```python
# tests/suites/acme_controller_tests/test_acme.py
@auto_configure_test
def test_acme_initialization(acme_controller_interface):
    result = acme_controller_interface.initialize()
    assert result.success
```

### Usage
```bash
export HARDWARE_PLATFORM=acme_test_bench
python run_tests.py --suite acme_controller_tests
```

This provides a complete, working integration that follows VORTEX patterns and best practices.