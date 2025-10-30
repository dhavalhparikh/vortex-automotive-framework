# VORTEX - Vehicle Operations Regression Testing EXecution

A configuration-driven, containerized automotive test framework that simplifies test creation by removing decorator complexity from test code.

## Features

- 🔧 **Configuration-Driven**: All test metadata managed via YAML - no decorators in test code
- 🐳 **Containerized**: Docker support with hardware device access
- 📊 **HTML Reporting**: Clean pytest-html reports with detailed logs
- 🚗 **Hardware Abstraction**: Support multiple ECU platforms via configuration
- ⚡ **Parallel Execution**: Run tests in parallel with pytest-xdist
- 🔗 **CI/CD Ready**: Jenkins, GitLab CI, GitHub Actions integration
- 📝 **Dynamic Decorators**: Pytest and Allure decorators applied automatically from config
- 🎯 **Smart Filtering**: Run tests by category, priority, platform, or suite

## Quick Start

### Prerequisites
- Docker (for containerized execution)
- Python 3.9+ (for local development)

### Running Tests with Docker

```bash
# Build the container
docker build -t automotive-tests .

# Run all smoke tests
docker run --rm \
  --device=/dev/ttyUSB0 \
  --device=/dev/can0 \
  -v $(pwd)/reports:/app/reports \
  automotive-tests

# Run specific category
docker run --rm \
  --device=/dev/can0 \
  -v $(pwd)/reports:/app/reports \
  automotive-tests --category smoke

# Run specific priority tests
docker run --rm \
  --device=/dev/can0 \
  -v $(pwd)/reports:/app/reports \
  automotive-tests --priority critical

# Run with specific hardware configuration
docker run --rm \
  --device=/dev/can0 \
  -v $(pwd)/reports:/app/reports \
  -e HARDWARE_PLATFORM=ecu_platform_a \
  automotive-tests
```

### Local Development

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run all tests
python run_tests.py

# Run by category/priority/suite
python run_tests.py --category smoke
python run_tests.py --priority critical
python run_tests.py --suite can_bus

# Run with HTML report
python run_tests.py --report html

# Run specific test suite directly
pytest tests/suites/can_bus/

# Run with specific hardware config
HARDWARE_PLATFORM=ecu_platform_a python run_tests.py
```

## Project Structure

```
project_vortex/
├── config/
│   ├── hardware/                    # Hardware platform configurations
│   │   ├── ecu_platform_a.yaml
│   │   ├── ecu_platform_b.yaml
│   │   └── mock_platform.yaml
│   ├── test_registry.yaml           # Test metadata configuration
│   └── pytest.ini                   # Pytest configuration
│
├── framework/
│   ├── core/
│   │   ├── hardware_abstraction.py  # HAL implementation
│   │   ├── config_loader.py         # Configuration management
│   │   ├── test_registry.py         # Test metadata management
│   │   ├── test_decorators.py       # Dynamic decorator application
│   │   ├── test_context.py          # Shared test context
│   │   └── types.py                 # Shared type definitions
│   ├── adapters/                    # Hardware interface adapters
│   │   ├── can_adapter.py           # CAN bus communication
│   │   ├── serial_adapter.py        # Serial/UART communication
│   │   ├── gpio_adapter.py          # GPIO control
│   │   └── mock_adapter.py          # Mock interfaces for testing
│   └── utils/
│       ├── logger.py                # Logging utilities
│       └── helpers.py               # Helper functions
│
├── tests/
│   ├── conftest.py                  # Pytest fixtures and configuration
│   ├── suites/
│   │   ├── can_bus/                 # CAN bus tests
│   │   ├── diagnostics/             # UDS/diagnostic tests
│   │   ├── network/                 # Network/Ethernet tests
│   │   └── system/                  # System-level tests
│
├── ci/
│   ├── jenkins/Jenkinsfile
│   ├── gitlab/.gitlab-ci.yml
│   └── github/workflow.yml
│
├── reports/                         # Generated test reports
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── run_tests.py                     # CLI test runner
├── CLAUDE.md                        # Development guide
└── README.md
```

## Configuration-Driven Test Framework

VORTEX uses a revolutionary approach where test metadata is managed through configuration, not decorators in code.

### Adding New Test Cases

1. **Write clean test code** - Just add the `@auto_configure_test` decorator:

```python
# tests/suites/can_bus/test_can_filters.py

from framework.core.test_decorators import auto_configure_test

@auto_configure_test
def test_can_filter_initialization(can_interface):
    """Test CAN filter setup"""
    result = can_interface.add_filter(0x100, 0x7FF)
    assert result.success, f"Failed to add filter: {result.error}"

@auto_configure_test
def test_can_multiple_filters(can_interface):
    """Test multiple CAN filters"""
    # Initialize interface
    init_result = can_interface.initialize()
    assert init_result.success

    # Add multiple filters
    for filter_id in [0x100, 0x200, 0x300]:
        result = can_interface.add_filter(filter_id, 0x7FF)
        assert result.success
```

2. **Configure test metadata** in `config/test_registry.yaml`:

```yaml
test_suites:
  can_bus:
    tests:
      - name: "test_can_filter_initialization"
        category: "smoke"
        priority: "high"
        platforms: ["all"]
        description: "Test CAN filter setup and configuration"
        requirements_hardware: false

      - name: "test_can_multiple_filters"
        category: "regression"
        priority: "medium"
        platforms: ["ecu_platform_a", "ecu_platform_b"]
        description: "Test multiple CAN filter management"
        requirements_hardware: true
```

That's it! No pytest markers, no allure decorators - everything is applied automatically from the configuration.

## Hardware Configuration

Define hardware platforms in YAML:

```yaml
# config/hardware/ecu_platform_a.yaml
platform:
  name: "ECU Platform A"
  version: "2.0"

interfaces:
  can:
    type: "socketcan"
    channel: "can0"
    bitrate: 500000
    
  serial:
    port: "/dev/ttyUSB0"
    baudrate: 115200

test_parameters:
  default_timeout: 5.0
  retry_count: 3
```

### Test Registry Configuration

The `config/test_registry.yaml` file defines:

- **Categories**: smoke, regression, integration, performance
- **Priorities**: critical, high, medium, low
- **Platforms**: all, ecu_platform_a, ecu_platform_b, mock_platform
- **Suites**: can_bus, diagnostics, network, system

### Running Specific Test Groups

```bash
# Run by category
python run_tests.py --category smoke
python run_tests.py --category regression

# Run by priority
python run_tests.py --priority critical
python run_tests.py --priority high

# Run by suite
python run_tests.py --suite can_bus
python run_tests.py --suite diagnostics

# Run with platform selection
export HARDWARE_PLATFORM=ecu_platform_a
python run_tests.py

# Combine filters
python run_tests.py --category smoke --priority critical
```

## Documentation

- [Adding Tests](docs/adding_tests.md)
- [Hardware Configuration](docs/hardware_config.md)
- [CI/CD Integration](docs/cicd_integration.md)
- [API Reference](docs/api_reference.md)

## License

MIT License
