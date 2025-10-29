# Automotive Smoke Test Framework

A modular, containerized smoke test framework for automotive systems testing across different hardware configurations.

## Features

- 🔧 **Modular Architecture**: Easy to add new test suites
- 🐳 **Containerized**: Docker support with hardware device access
- 📊 **Rich Reporting**: Allure reports with history, trends, and detailed logs
- 🚗 **Hardware Abstraction**: Support multiple ECU platforms via configuration
- ⚡ **Parallel Execution**: Run tests in parallel with pytest-xdist
- 🔗 **CI/CD Ready**: Jenkins, GitLab CI, GitHub Actions integration
- 📝 **Dependency Management**: Control test execution order
- 🎯 **Flexible Markers**: Organize tests by domain, priority, platform

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

# Run specific test suite
docker run --rm \
  --device=/dev/can0 \
  -v $(pwd)/reports:/app/reports \
  automotive-tests -m can_bus

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
pytest

# Run specific markers
pytest -m smoke
pytest -m "can_bus and smoke"

# Run with Allure report
pytest --alluredir=./reports/allure-results
allure serve ./reports/allure-results

# Run specific suite
pytest tests/suites/can_bus/

# Run with specific hardware config
HARDWARE_PLATFORM=ecu_platform_a pytest
```

## Project Structure

```
automotive-test-framework/
├── config/
│   ├── hardware/                    # Hardware platform configurations
│   │   ├── ecu_platform_a.yaml
│   │   ├── ecu_platform_b.yaml
│   │   └── mock_platform.yaml
│   └── pytest.ini                   # Pytest configuration
│
├── framework/
│   ├── core/
│   │   ├── hardware_abstraction.py  # HAL implementation
│   │   ├── config_loader.py         # Configuration management
│   │   └── test_context.py          # Shared test context
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
└── README.md
```

## Adding New Test Cases

Create a new test file in the appropriate suite:

```python
# tests/suites/can_bus/test_can_filters.py

import pytest
import allure

@allure.feature('CAN Bus')
@allure.story('Message Filtering')
class TestCANFilters:
    
    @pytest.mark.smoke
    @pytest.mark.can_bus
    @allure.title("Test CAN filter initialization")
    def test_filter_initialization(self, hardware):
        """Verify CAN filters can be configured"""
        can = hardware.can
        
        with allure.step("Configure message filter for ID 0x100"):
            result = can.add_filter(0x100)
            assert result.success, f"Failed to add filter: {result.error}"
        
        with allure.step("Verify filter is active"):
            filters = can.get_filters()
            assert 0x100 in filters
```

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

Select platform:
```bash
export HARDWARE_PLATFORM=ecu_platform_a
pytest
```

## Documentation

- [Adding Tests](docs/adding_tests.md)
- [Hardware Configuration](docs/hardware_config.md)
- [CI/CD Integration](docs/cicd_integration.md)
- [API Reference](docs/api_reference.md)

## License

MIT License
