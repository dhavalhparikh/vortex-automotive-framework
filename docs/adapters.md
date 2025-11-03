# Adapter Development Guide

Adapters are hardware-specific drivers that implement communication with different devices and protocols. VORTEX provides a one-command generator to create production-ready adapters.

## Quick Start: Generate an Adapter

Create a complete adapter with a single command:

```bash
# Generate CLI adapter for serial/SSH communication
python scripts/create_adapter.py cli --device /dev/ttyUSB0 --methods "execute_command,send_ssh_command" --tests

# Generate Ethernet adapter with custom methods
python scripts/create_adapter.py ethernet --device /dev/eth0 --methods "send_packet,receive_packet,set_speed" --tests --priority high

# Generate basic adapter (minimal implementation)
python scripts/create_adapter.py my_device
```

## Generator Options

```bash
python scripts/create_adapter.py <name> [options]

Options:
  --device PATH          Custom device path (auto-guessed if not provided)
  --methods LIST         Comma-separated custom methods to generate
  --tests                Generate comprehensive test suite
  --priority LEVEL       Test priority: critical, high, medium, low
  --category TYPE        Test category: smoke, regression, integration, performance
  --description TEXT     Custom adapter description
```

## What Gets Generated

The generator creates:

1. **`framework/adapters/{name}_adapter.py`** - Complete adapter implementation
2. **`tests/suites/{name}_tests/test_{name}_comprehensive.py`** - Test suite (if --tests)
3. **Updated `config/test_registry.yaml`** - Test metadata
4. **Hardware config section** in appropriate YAML files

## Adapter Structure

### Main Adapter Class
```python
class MyDeviceAdapter:
    def __init__(self, config):
        """Initialize with hardware configuration"""
        self.config = config
        self.device_path = config.get('device_path', '/dev/mydevice0')
        self._is_initialized = False

    def initialize(self) -> OperationResult:
        """Initialize the device connection"""
        # Implementation here
        self._is_initialized = True
        return OperationResult(success=True, log="Device initialized")

    def cleanup(self) -> OperationResult:
        """Clean up device connection"""
        # Implementation here
        self._is_initialized = False
        return OperationResult(success=True, log="Device cleaned up")

    def is_ready(self) -> bool:
        """Check if adapter is ready for operations"""
        return self._is_initialized

    def get_status(self) -> str:
        """Get current adapter status"""
        return "active" if self.is_ready() else "inactive"

    # Custom methods based on your device capabilities
    def send_data(self, data: bytes) -> OperationResult:
        """Send data to device"""
        if not self.is_ready():
            return OperationResult(success=False, error="Not initialized")
        # Implementation here
```

### Mock Adapter Class
```python
class MockMyDeviceAdapter(MyDeviceAdapter):
    """Mock adapter for testing without actual hardware"""

    def __init__(self, config):
        super().__init__(config)
        self._mock_responses = {}

    def initialize(self) -> OperationResult:
        """Mock initialization - always succeeds"""
        self._is_initialized = True
        return OperationResult(success=True, log="Mock device initialized")

    def send_data(self, data: bytes) -> OperationResult:
        """Mock data sending"""
        if not self.is_ready():
            return OperationResult(success=False, error="Not initialized")

        # Mock implementation
        response = f"Mock response for: {data.hex()}"
        return OperationResult(success=True, data=response)
```

## Auto-Discovery Requirements

For the adapter to be auto-discovered by the framework:

1. **File Location**: `framework/adapters/{name}_adapter.py`
2. **Class Name**: `{Name}Adapter` (e.g., `MyDeviceAdapter`)
3. **Mock Class**: `Mock{Name}Adapter` (optional, for testing)
4. **Configuration**: Hardware config section named `{name}`

## Configuration Integration

Add your adapter configuration to hardware YAML files:

```yaml
# config/hardware/my_platform.yaml
interfaces:
  my_device:
    type: "custom"  # or "mock" for testing
    device_path: "/dev/mydevice0"
    baudrate: 115200
    timeout: 5.0
    custom_setting: "value"
```

## Using Your Adapter in Tests

Once created, your adapter is immediately available:

```python
from framework.core.test_decorators import auto_configure_test

@auto_configure_test
def test_my_device_functionality(my_device_interface):
    """Test automatically gets the adapter via fixture"""
    # Initialize
    result = my_device_interface.initialize()
    assert result.success

    # Use device
    result = my_device_interface.send_data(b"test_data")
    assert result.success

    # Cleanup happens automatically
```

## Best Practices

### Error Handling
```python
def some_operation(self) -> OperationResult:
    try:
        if not self.is_ready():
            return OperationResult(success=False, error="Device not initialized")

        # Device operation here
        result = self._device.do_something()

        return OperationResult(
            success=True,
            data=result,
            log=f"Operation completed: {result}"
        )
    except Exception as e:
        return OperationResult(
            success=False,
            error=f"Operation failed: {str(e)}"
        )
```

### Configuration Validation
```python
def __init__(self, config):
    self.config = config

    # Validate required config
    required_fields = ['device_path', 'baudrate']
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required config: {field}")

    self.device_path = config['device_path']
    self.baudrate = config['baudrate']
```

### Resource Management
```python
def initialize(self) -> OperationResult:
    try:
        self._connection = open_device(self.device_path)
        self._is_initialized = True
        return OperationResult(success=True)
    except Exception as e:
        return OperationResult(success=False, error=str(e))

def cleanup(self) -> OperationResult:
    try:
        if hasattr(self, '_connection') and self._connection:
            self._connection.close()
        self._is_initialized = False
        return OperationResult(success=True)
    except Exception as e:
        return OperationResult(success=False, error=str(e))
```

## Advanced Features

### Custom Mock Responses
```python
class MockMyDeviceAdapter(MyDeviceAdapter):
    def set_mock_response(self, command: str, response: str):
        """Set custom mock response for testing"""
        self._mock_responses[command] = response

    def send_command(self, command: str) -> OperationResult:
        if command in self._mock_responses:
            response = self._mock_responses[command]
        else:
            response = f"Mock response for: {command}"

        return OperationResult(success=True, data=response)
```

### Device Discovery
```python
@classmethod
def discover_devices(cls) -> List[str]:
    """Discover available devices of this type"""
    devices = []
    for i in range(10):
        device_path = f"/dev/mydevice{i}"
        if os.path.exists(device_path):
            devices.append(device_path)
    return devices
```

## Troubleshooting

### Adapter Not Found
- Check file naming: `{name}_adapter.py`
- Check class naming: `{Name}Adapter`
- Check file location: `framework/adapters/`

### Configuration Issues
- Verify YAML syntax in hardware config
- Check interface name matches adapter name
- Ensure required config fields are present

### Mock Adapter Not Used
- Set `HARDWARE_PLATFORM=mock_platform`
- Check mock class exists: `Mock{Name}Adapter`
- Verify mock adapter inherits from main adapter

### Test Fixtures Not Available
- Check `{name}_interface` parameter naming
- Verify adapter is properly auto-discovered
- Check hardware platform configuration