# Framework Architecture

VORTEX uses a layered architecture that provides clean separation between test logic, hardware abstraction, and device-specific implementations.

## Architecture Overview

```
┌─────────────────────────────────────────────┐
│                Test Layer                   │  ← Configuration-driven tests
├─────────────────────────────────────────────┤
│              Test Registry                  │  ← YAML-based test metadata
├─────────────────────────────────────────────┤
│           Hardware Abstraction             │  ← Unified hardware interface
├─────────────────────────────────────────────┤
│               Adapters                      │  ← Hardware-specific drivers
├─────────────────────────────────────────────┤
│            Hardware/Mock                    │  ← Real devices or simulation
└─────────────────────────────────────────────┘
```

## Layer Details

### Test Layer
**Purpose**: Clean, decorator-free test functions
**Key Feature**: Only needs `@auto_configure_test` decorator
**Location**: `tests/suites/`

```python
@auto_configure_test
def test_can_initialization(can_interface):
    """Test CAN interface initialization"""
    result = can_interface.initialize()
    assert result.success
```

**Benefits**:
- No pytest markers or allure decorators in test code
- Clean, readable test functions
- All metadata managed externally via YAML

### Test Registry
**Purpose**: Centralized metadata management via YAML
**Key Feature**: Dynamic decorator application at runtime
**Location**: `config/test_registry.yaml`

**Controls**:
- Categories (smoke, regression, integration, performance)
- Priorities (critical, high, medium, low)
- Platforms (all, specific platforms, mock_platform)
- Descriptions and requirements

**Example**:
```yaml
test_suites:
  can_bus:
    tests:
      - name: "test_can_initialization"
        category: "smoke"
        priority: "critical"
        platforms: ["all"]
        description: "Test CAN interface initialization"
```

### Hardware Abstraction Layer (HAL)
**Purpose**: Unified interface to all hardware
**Key Feature**: Auto-discovery of adapters via `{name}_interface`
**Location**: `framework/core/hardware_abstraction.py`

**Auto-Discovery**:
```python
# Automatically loads CLIAdapter or MockCliAdapter
cli = hardware.cli_interface

# Automatically loads EthernetAdapter or MockEthernetAdapter
eth = hardware.ethernet_interface
```

**Features**:
- Dynamic adapter loading
- Mock/real adapter selection based on platform
- Automatic configuration injection
- Centralized cleanup

### Adapters
**Purpose**: Hardware-specific drivers and communication
**Key Feature**: Template-based creation with auto-discovery
**Location**: `framework/adapters/`
**Pattern**: `{name}_adapter.py` with `{Name}Adapter` class

**Adapter Structure**:
```python
class CliAdapter:
    def __init__(self, config):
        # Hardware-specific initialization

    def initialize(self) -> OperationResult:
        # Connect to hardware

    def execute_command(self, command: str) -> OperationResult:
        # Hardware-specific implementation

class MockCliAdapter(CliAdapter):
    # Mock implementation for testing
```

**Auto-Discovery Requirements**:
- File named `{adapter_name}_adapter.py`
- Class named `{AdapterName}Adapter`
- Optional `Mock{AdapterName}Adapter` for testing
- Configuration section in hardware YAML

### Hardware/Mock Layer
**Purpose**: Actual devices or simulation
**Key Feature**: Seamless switching between real/mock hardware
**Control**: `HARDWARE_PLATFORM` environment variable

**Platform Selection**:
```bash
# Use real hardware
export HARDWARE_PLATFORM=ecu_platform_a

# Use mock devices (CI/CD)
export HARDWARE_PLATFORM=mock_platform
```

## Auto-Discovery System

The framework automatically discovers and loads adapters without manual registration:

1. **Adapter Discovery**: Scans `framework/adapters/` for `*_adapter.py` files
2. **Interface Access**: `hardware.{name}_interface` automatically works
3. **Test Fixtures**: `{name}_interface` parameters automatically provided
4. **Mock Support**: `Mock{Name}Adapter` classes automatically used on mock platform
5. **Configuration**: Standard YAML config in `config/hardware/`

## Configuration Flow

```
Platform Selection (env var)
         ↓
Hardware Config Loading (YAML)
         ↓
Test Registry Loading (YAML)
         ↓
Dynamic Adapter Creation
         ↓
Test Execution with Auto-Fixtures
```

## Benefits

- **Zero Boilerplate**: Tests need only `@auto_configure_test`
- **Platform Agnostic**: Same tests run on real hardware or mocks
- **Configuration Driven**: All metadata external to test code
- **Extensible**: New adapters auto-discovered
- **CI/CD Ready**: Mock platform for automated testing