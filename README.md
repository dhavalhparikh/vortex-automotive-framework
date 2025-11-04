# VORTEX - Vehicle Operations Regression Testing EXecution

A configuration-driven, containerized automotive test framework that simplifies test creation by separating test logic from metadata management.

## Features

- 🔧 **Configuration-Driven**: All test metadata managed via YAML - no decorators in test code
- 🐳 **Containerized**: Docker support with hardware device access
- 📊 **HTML Reporting**: Clean pytest-html reports with detailed logs
- 🚗 **Hardware Abstraction**: Support multiple ECU platforms via configuration
- ⚡ **Parallel Execution**: Run tests in parallel with pytest-xdist
- 🔗 **CI/CD Ready**: Jenkins, GitLab CI, GitHub Actions integration
- 🎯 **Smart Filtering**: Run tests by category, priority, platform, suite, or execution profile
- 📋 **Execution Profiles**: Predefined test configurations for different scenarios (smoke, hil, nightly)
- 🚀 **One-Command Adapters**: Generate production-ready adapters instantly

## Quick Start

### Prerequisites
- **Docker** (recommended) - all dependencies contained in container
- OR Python 3.9+ (for local development)

### Running Tests with Docker (Recommended)

```bash
# Build the container
docker build -t automotive-tests .

# Run smoke tests using execution profile (no hardware required)
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  automotive-tests --exec-profile smoke

# Run specific test suite
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  automotive-tests --suite can_bus

# Run with real hardware (requires hardware devices)
docker run --rm \
  --device=/dev/can0 \
  --device=/dev/ttyUSB0 \
  -e HARDWARE_PLATFORM=ecu_platform_a \
  -v $(pwd)/reports:/app/reports \
  automotive-tests --priority critical

# View reports
cd reports && python3 -m http.server 8000
# Open: http://localhost:8000/report.html
```

### Docker Testing (RECOMMENDED)

```bash
# Auto-discovers hardware devices from platform config - no manual --device mapping!
./auto_test.sh my_platform --exec-profile smoke
./auto_test.sh custom_cli_platform --exec-profile hil

# Advanced Docker usage
python scripts/auto_docker.py run --platform my_platform --exec-profile smoke
python scripts/auto_docker.py compose --platform my_platform && docker-compose up
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests locally (requires hardware setup)
python run_tests.py --exec-profile smoke
python run_tests.py --exec-profile hil --platform ecu_platform_a
```

## Project Structure

```
project_vortex/
├── config/                          # Configuration files
│   ├── hardware/                    # Hardware platform definitions
│   ├── test_registry/               # Split test registry structure
│   │   ├── suites/                  # Test definitions by functionality
│   │   ├── execution/               # Execution profiles (smoke, hil, nightly)
│   │   └── _globals.yaml            # Shared configuration
│   └── test_registry.yaml           # Legacy test registry (if not migrated)
├── framework/                       # Core framework
│   ├── core/                        # Core components (HAL, config, decorators)
│   ├── adapters/                    # Hardware adapters (CAN, serial, CLI, etc.)
│   └── utils/                       # Utilities and helpers
├── tests/                           # Test suites
│   └── suites/                      # Organized test suites
├── scripts/                         # Utility scripts
├── docs/                            # Documentation
├── reports/                         # Generated test reports
└── run_tests.py                     # Main test runner
```

## Writing Tests

VORTEX uses a configuration-driven approach where test metadata is managed externally:

```python
from framework.core.test_decorators import auto_configure_test

@auto_configure_test
def test_can_initialization(can_interface):
    """Test CAN interface initialization"""
    result = can_interface.initialize()
    assert result.success, f"Failed: {result.error}"
```

Configure test metadata in `config/test_registry/suites/can_bus.yaml`:

```yaml
suite_info:
  name: "can_bus"
  description: "CAN bus communication tests"

tests:
  - name: "test_can_initialization"
    category: "smoke"
    priority: "critical"
    platforms: ["all"]
```

Create execution profiles in `config/test_registry/execution/smoke.yaml`:

```yaml
execution_profile:
  name: "smoke"
  description: "Critical smoke tests for fast feedback"

include:
  - suite: "can_bus"
    tests: ["test_can_initialization"]
```

No pytest markers or decorators needed - everything applied automatically!

## Adding New Adapters

Generate production-ready adapters with one command:

```bash
# Generate CLI adapter for serial/SSH communication
python scripts/create_adapter.py cli --device /dev/ttyUSB0 --methods "execute_command,send_ssh_command" --tests

# Generates:
# ✅ framework/adapters/cli_adapter.py (production-ready)
# ✅ tests/suites/cli_tests/ (comprehensive test suite)
# ✅ Updated config/test_registry.yaml (test metadata)
# ✅ Mock adapter for CI/CD testing
```

The adapter is immediately available for use:

```python
@auto_configure_test
def test_my_cli_feature(cli_interface):  # Auto-fixture!
    result = cli_interface.execute_command("show version")
    assert result.success
```

## Hardware Configuration

Define hardware platforms in YAML:

```yaml
# config/hardware/my_platform.yaml
platform:
  name: "My ECU Platform"
  version: "2.0"

interfaces:
  can:
    type: "socketcan"
    channel: "can0"
    bitrate: 500000

  cli:
    type: "serial"
    device_path: "/dev/ttyUSB0"
    baudrate: 115200

test_parameters:
  default_timeout: 5.0
  retry_count: 3
```

## Framework Architecture

```
┌─────────────────────────────────────────────┐
│                Test Layer                   │  ← Clean test functions
├─────────────────────────────────────────────┤
│              Test Registry                  │  ← YAML metadata
├─────────────────────────────────────────────┤
│           Hardware Abstraction             │  ← Auto-discovery
├─────────────────────────────────────────────┤
│               Adapters                      │  ← Hardware drivers
├─────────────────────────────────────────────┤
│            Hardware/Mock                    │  ← Real or simulated
└─────────────────────────────────────────────┘
```

## Running Tests

### Using Execution Profiles (Recommended)

```bash
# List available execution profiles
python run_tests.py --list-profiles

# Run execution profiles for different scenarios
python run_tests.py --exec-profile smoke      # Fast smoke tests
python run_tests.py --exec-profile hil        # Hardware-in-the-loop tests
python run_tests.py --exec-profile nightly    # Comprehensive nightly run
python run_tests.py --exec-profile regression # Full regression suite

# Run profile with specific platform
python run_tests.py --exec-profile hil --platform ecu_platform_a

# Filter tests within profiles
python run_tests.py --exec-profile smoke --suite can_bus
python run_tests.py --exec-profile regression --priority critical
```

### Traditional Usage (Still Supported)

```bash
# Run by category
python run_tests.py --category smoke

# Run by priority
python run_tests.py --priority critical

# Run specific suite
python run_tests.py --suite can_bus

# Run with hardware platform
export HARDWARE_PLATFORM=ecu_platform_a
python run_tests.py --category regression
```

## User Integration

Users can easily integrate their own hardware and tests by following the template/example approach:

1. **Copy and modify** existing platform configs
2. **Create custom adapters** using the generator
3. **Add test suites** following existing patterns
4. **Configure in YAML** without touching test code

See the [Integration Guide](docs/integration.md) for detailed examples.

## Documentation

- **[Architecture](docs/architecture.md)** - Framework layers and auto-discovery
- **[Adapters](docs/adapters.md)** - Creating and using hardware adapters
- **[Configuration](docs/configuration.md)** - Hardware platforms and test registry
- **[Execution Profiles](docs/execution_profiles.md)** - Organizing tests for different scenarios
- **[Testing](docs/testing.md)** - Writing and running tests
- **[Integration](docs/integration.md)** - Adding your own hardware and tests
- **[Scripts](docs/scripts.md)** - Available utility scripts

## License

MIT License
