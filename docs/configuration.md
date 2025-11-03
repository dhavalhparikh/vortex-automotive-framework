# Configuration Guide

VORTEX uses YAML configuration files to define hardware platforms, test metadata, and framework behavior. All configuration is external to test code, making tests platform-agnostic.

## Configuration Structure

```
config/
├── hardware/                    # Hardware platform definitions
│   ├── ecu_platform_a.yaml
│   ├── ecu_platform_b.yaml
│   └── mock_platform.yaml
├── test_registry.yaml           # Test metadata and organization
└── pytest.ini                   # Pytest configuration
```

## Hardware Configuration

Hardware configurations define the devices, interfaces, and parameters for different test platforms.

### Platform Selection

```bash
# Select hardware platform via environment variable
export HARDWARE_PLATFORM=ecu_platform_a  # Real hardware
export HARDWARE_PLATFORM=mock_platform   # Mock/simulation
```

### Hardware Config Structure

```yaml
# config/hardware/ecu_platform_a.yaml
platform:
  name: "ECU Platform A"
  version: "2.0"
  vendor: "Automotive Corp"
  description: "Primary ECU testing platform"

interfaces:
  can:
    type: "socketcan"
    channel: "can0"
    bitrate: 500000
    fd_enabled: false

  serial:
    type: "uart"
    port: "/dev/ttyUSB0"
    baudrate: 115200
    timeout: 5.0

  ethernet:
    type: "standard"
    interface: "eth0"
    ip_address: "192.168.1.100"

  cli:
    type: "serial"
    connection_type: "serial"
    device_path: "/dev/ttyUSB0"
    baudrate: 115200
    timeout: 5.0
    command_timeout: 10.0
    prompt_pattern: '[\\$#>]\\s*$'

sensors:
  temperature:
    type: "i2c"
    address: 0x48
    range: [-40, 125]

  accelerometer:
    type: "spi"
    device: "/dev/spidev0.0"
    axes: ["x", "y", "z"]

diagnostics:
  protocol: "uds"
  transport: "can"
  isotp:
    tx_id: 0x7E0
    rx_id: 0x7E8

test_parameters:
  default_timeout: 10.0
  retry_count: 3
  log_level: "INFO"

power:
  nominal_voltage: 12.0
  voltage_range: [11.0, 14.0]

notes: |
  Configuration for ECU Platform A.
  Requires CAN interface setup: sudo ip link set can0 type can bitrate 500000
  Serial permissions: sudo chmod 666 /dev/ttyUSB0
```

### Mock Platform Configuration

Mock platforms simulate hardware for CI/CD and development:

```yaml
# config/hardware/mock_platform.yaml
platform:
  name: "Mock ECU Platform"
  version: "1.0"
  description: "Simulated hardware for testing"

interfaces:
  can:
    type: "mock"
    channel: "vcan0"
    bitrate: 500000

  serial:
    type: "mock"
    port: "mock_serial"
    baudrate: 115200

  cli:
    type: "mock"
    connection_type: "serial"
    device_path: "/dev/ttyUSB0"  # Not used in mock
    baudrate: 115200

test_parameters:
  default_timeout: 1.0  # Faster for mocks
  retry_count: 1
  simulate_delays: false
```

## Test Registry Configuration

The test registry defines test metadata, organization, and execution parameters.

### Test Registry Structure

```yaml
# config/test_registry.yaml
test_suites:
  can_bus:
    description: "CAN bus communication tests"
    platforms: ["ecu_platform_a", "ecu_platform_b", "mock_platform"]
    tests:
      - name: "test_can_initialization"
        category: "smoke"
        priority: "critical"
        description: "Test CAN interface initialization"
        platforms: ["all"]

      - name: "test_send_can_message"
        category: "smoke"
        priority: "critical"
        description: "Test sending CAN messages"
        platforms: ["all"]

      - name: "test_receive_can_message"
        category: "regression"
        priority: "high"
        description: "Test receiving CAN messages"
        platforms: ["ecu_platform_a", "ecu_platform_b"]
        requirements_hardware: true

  cli_tests:
    description: "CLI adapter tests"
    platforms: ["mock_platform"]
    tests:
      - name: "test_cli_execute_command"
        category: "smoke"
        priority: "high"
        description: "Test CLI command execution"
        requirements_hardware: false

# Test Categories
categories:
  smoke:
    description: "Critical tests that must pass"
    max_duration: "5m"

  regression:
    description: "Comprehensive test suite"
    max_duration: "30m"

  integration:
    description: "Cross-component integration tests"
    max_duration: "15m"

  performance:
    description: "Performance and load tests"
    max_duration: "60m"

# Priority Levels
priorities:
  critical:
    description: "Must-pass tests"
    weight: 100

  high:
    description: "Important tests"
    weight: 80

  medium:
    description: "Standard tests"
    weight: 60

  low:
    description: "Nice-to-have tests"
    weight: 40
```

### Test Metadata Fields

- **name**: Test function name (must match actual function)
- **category**: Test category (smoke, regression, integration, performance)
- **priority**: Test priority (critical, high, medium, low)
- **platforms**: Target platforms (["all"] or specific platforms)
- **description**: Human-readable test description
- **requirements_hardware**: Whether test needs real hardware

## Adding Custom Configurations

### New Hardware Platform

1. Create new YAML file:
```bash
# config/hardware/my_platform.yaml
platform:
  name: "My Custom Platform"
  version: "1.0"

interfaces:
  # Define your interfaces here
  my_device:
    type: "custom"
    device_path: "/dev/mydevice0"
    custom_setting: "value"
```

2. Use the platform:
```bash
export HARDWARE_PLATFORM=my_platform
python run_tests.py
```

### New Interface Configuration

Add interface configuration to existing platforms:

```yaml
interfaces:
  my_new_device:
    type: "custom"
    device_path: "/dev/mynewdevice0"
    baudrate: 9600
    protocol: "modbus"
    slave_id: 1
    custom_parameters:
      register_count: 100
      byte_order: "big_endian"
```

### Test Suite Configuration

Add new test suite to test registry:

```yaml
test_suites:
  my_test_suite:
    description: "My custom test suite"
    platforms: ["my_platform", "mock_platform"]
    tests:
      - name: "test_my_functionality"
        category: "smoke"
        priority: "high"
        description: "Test my custom functionality"
        platforms: ["all"]
```

## Configuration Validation

The framework validates configurations on startup:

- **Required Fields**: Platform name, interface types
- **Valid Values**: Categories, priorities, platform names
- **File Format**: Valid YAML syntax
- **Cross-References**: Test names match actual functions

### Common Validation Errors

```bash
# Invalid YAML syntax
ERROR: Invalid YAML in config/hardware/my_platform.yaml

# Missing required fields
ERROR: Platform config missing required field: name

# Invalid test reference
ERROR: Test 'test_nonexistent' not found in test suite

# Invalid platform reference
ERROR: Platform 'unknown_platform' not found
```

## Environment Variables

Control framework behavior via environment variables:

```bash
# Platform selection
export HARDWARE_PLATFORM=mock_platform

# Config directory override
export VORTEX_CONFIG_DIR=/path/to/custom/configs

# Log level override
export VORTEX_LOG_LEVEL=DEBUG

# Test timeout override
export VORTEX_TEST_TIMEOUT=30
```

## Configuration Best Practices

### Hardware Platforms
- Use descriptive platform names
- Include version information
- Document required setup steps
- Provide mock equivalents

### Interface Configuration
- Use consistent naming conventions
- Include all required parameters
- Document custom settings
- Validate device paths exist

### Test Registry
- Group related tests in suites
- Use clear, descriptive names
- Set appropriate priorities
- Document hardware requirements

### Mock Configurations
- Mirror real platform structure
- Use faster timeouts
- Disable unnecessary delays
- Provide realistic mock data