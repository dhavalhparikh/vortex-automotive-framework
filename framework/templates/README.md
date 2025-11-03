# Adapter Templates

This directory contains templates for creating new hardware adapters in the VORTEX framework.

## Quick Start

### 1. Copy Template Files

```bash
# Create your adapter
cp framework/templates/adapter_template.py framework/adapters/ethernet_adapter.py

# Create tests (optional)
cp framework/templates/test_template.py tests/suites/ethernet/test_ethernet.py
```

### 2. Replace Placeholders

In your copied files, replace these placeholders:

| Placeholder | Example | Description |
|-------------|---------|-------------|
| `{{ADAPTER_NAME}}` | `Ethernet` | Human-readable adapter name |
| `{{ADAPTER_CLASS}}` | `EthernetAdapter` | Python class name |
| `{{adapter_name}}` | `ethernet` | Lowercase adapter name |
| `{{DEVICE_PATH}}` | `/dev/eth0` | Default device path |
| `{{PLATFORM_NAME}}` | `ECU Platform with Ethernet` | Platform description |

### 3. Add Configuration

Add interface config to your platform file:

```yaml
# config/hardware/your_platform.yaml
interfaces:
  ethernet:  # Framework auto-discovers this
    device_path: "/dev/eth0"
    speed: "1000"
```

### 4. Add Test Registry (if using tests)

```yaml
# config/test_registry.yaml
test_suites:
  ethernet_tests:
    description: "Ethernet interface tests"
    platforms: ["all"]
    tests:
      - name: "test_ethernet_initialization"
        category: "smoke"
        priority: "critical"
        platforms: ["all"]
        description: "Test Ethernet interface initialization"
```

### 5. Use Your Adapter

```python
# In tests
@auto_configure_test
def test_my_ethernet_feature(ethernet_interface):
    result = ethernet_interface.initialize()
    assert result.success

    result = ethernet_interface.send_data("test")
    assert result.success
```

## Template Files

### `adapter_template.py`
- Complete adapter implementation template
- Includes both real and mock adapter classes
- All common methods with TODO placeholders
- Comprehensive error handling

### `test_template.py`
- Complete test suite template
- Tests for all common adapter operations
- Includes stress tests and error handling tests
- Platform-specific test examples

### `config_template.yaml`
- Hardware configuration examples
- Test registry configuration
- Complete platform configuration example
- Commented configuration options

## Auto-Discovery Features

The framework automatically:

✅ **Discovers adapters** - Put `*_adapter.py` in `framework/adapters/`
✅ **Creates interfaces** - Access via `hardware.{name}_interface`
✅ **Generates fixtures** - Use `{name}_interface` in tests
✅ **Loads configurations** - Reads from hardware config YAML

No manual HAL editing required!

## Implementation Tips

### Adapter Best Practices
1. **Always inherit from `BaseAdapter`**
2. **Implement required methods**: `initialize()`, `cleanup()`, `is_ready()`
3. **Use `OperationResult`** for all return values
4. **Add comprehensive error handling**
5. **Create mock version** for testing without hardware

### Test Best Practices
1. **Use `@auto_configure_test`** decorator
2. **Test initialization/cleanup** in every test class
3. **Include error handling tests**
4. **Add platform-specific tests** when needed
5. **Use descriptive test names** matching registry

### Configuration Best Practices
1. **Provide sensible defaults** in adapter constructor
2. **Document all configuration options**
3. **Use consistent parameter names** across adapters
4. **Add platform-specific parameters** as needed

## Example: Creating Ethernet Adapter

```bash
# 1. Copy template
cp framework/templates/adapter_template.py framework/adapters/ethernet_adapter.py

# 2. Edit ethernet_adapter.py:
#    - Replace {{ADAPTER_NAME}} with "Ethernet"
#    - Replace {{ADAPTER_CLASS}} with "EthernetAdapter"
#    - Replace {{adapter_name}} with "ethernet"
#    - Replace {{DEVICE_PATH}} with "/dev/eth0"
#    - Implement TODO methods

# 3. Add to platform config
echo "interfaces:
  ethernet:
    device_path: '/dev/eth0'
    speed: '1000'" >> config/hardware/your_platform.yaml

# 4. Use in tests
# hardware.ethernet_interface is now available!
```

## Advanced Features

### Custom Methods
Add any methods your adapter needs:
```python
def send_packet(self, packet_data: bytes) -> OperationResult:
def set_speed(self, speed: str) -> OperationResult:
def get_link_status(self) -> OperationResult:
```

### Platform-Specific Behavior
Use configuration to handle platform differences:
```python
def initialize(self) -> OperationResult:
    if self.config.get('use_hardware_acceleration', False):
        # Enable hardware acceleration
        pass
```

### Mock Adapter Customization
Customize mock behavior for testing:
```python
class MockEthernetAdapter(EthernetAdapter):
    def send_packet(self, data):
        # Custom mock behavior
        return OperationResult(success=True, data=f"mock_echo_{data}")
```

## Need Help?

1. **Check existing adapters** in `framework/adapters/` for examples
2. **Review test patterns** in `tests/suites/`
3. **See configuration examples** in `config/hardware/`
4. **Read framework documentation** in `README.md`