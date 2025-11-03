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
- **Docker** (recommended) - all dependencies contained in container
- OR Python 3.9+ (for local development)

### Running Tests with Docker (Recommended)

```bash
# Build the container (includes all dependencies)
docker build -t automotive-tests .

# Run all smoke tests (no hardware required - uses mock adapters)
docker run --rm \
  -v $(pwd)/reports:/app/reports \
  automotive-tests --category smoke

# Run with mock platform (explicitly)
docker run --rm \
  -e HARDWARE_PLATFORM=mock_platform \
  -v $(pwd)/reports:/app/reports \
  automotive-tests --category smoke

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

# View reports after run
cd reports && python3 -m http.server 8000
# Open: http://localhost:8000/report.html
```

### Local Development (Optional)

**Note:** Docker is recommended to avoid installing dependencies on your system.

```bash
# Only if you want to develop locally without Docker:

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install all Python dependencies
pip install -r requirements.txt

# Install system dependencies (Linux)
sudo apt-get install can-utils iproute2 i2c-tools

# Run tests locally
python run_tests.py --category smoke
python run_tests.py --priority critical
python run_tests.py --suite can_bus

# Run with specific hardware config
HARDWARE_PLATFORM=mock_platform python run_tests.py
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

## Adding Custom Dependencies

### Python Packages (pip-based)

**Add to requirements.txt:**
```txt
# Your custom packages
your-company-diagnostic-lib==1.2.0
automotive-tools>=2.0.0

# From private PyPI
--extra-index-url https://your-company.com/pypi/simple/
private-automotive-package==1.0.0

# From Git repositories
git+https://github.com/your-org/automotive-utils.git@v1.5.0
```

**Or add directly to Dockerfile:**
```dockerfile
# After the existing pip install line, add:
RUN pip install --no-cache-dir \
    your-diagnostic-tool==1.0.0 \
    automotive-protocol-lib>=2.1.0
```

### System Dependencies (apt packages)

**Add to Dockerfile:**
```dockerfile
# Add your system packages to the existing RUN command:
RUN apt-get update && apt-get install -y \
    can-utils \
    iproute2 \
    your-custom-package \      # Add here
    libsomelib-dev \          # Add here
    && rm -rf /var/lib/apt/lists/*
```

### Custom Binaries/Tools from URLs

**Add to Dockerfile:**
```dockerfile
# Download and install custom tools
RUN wget https://your-company.com/tools/diagnostic-tool-v1.2.tar.gz -O /tmp/tool.tar.gz && \
    tar -xzf /tmp/tool.tar.gz -C /opt/ && \
    ln -s /opt/diagnostic-tool-v1.2/bin/diag-tool /usr/local/bin/diag-tool && \
    rm /tmp/tool.tar.gz

# Or for .deb packages
RUN wget https://releases.company.com/automotive-scanner_1.0_amd64.deb -O /tmp/scanner.deb && \
    dpkg -i /tmp/scanner.deb || apt-get install -f -y && \
    rm /tmp/scanner.deb
```

## Framework Architecture

### Layer Overview

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

### **Test Layer**
- **Purpose**: Clean, decorator-free test functions
- **Key Feature**: Only needs `@auto_configure_test` decorator
- **Location**: `tests/suites/`
- **Example**: `test_can_initialization(can_interface)`

### **Test Registry**
- **Purpose**: Centralized metadata management via YAML
- **Key Feature**: Dynamic decorator application at runtime
- **Location**: `config/test_registry.yaml`
- **Controls**: Categories, priorities, platforms, descriptions

### **Hardware Abstraction Layer (HAL)**
- **Purpose**: Unified interface to all hardware
- **Key Feature**: Auto-discovery of adapters via `{name}_interface`
- **Location**: `framework/core/hardware_abstraction.py`
- **Usage**: `hardware.ethernet_interface` → auto-loads `EthernetAdapter`

### **Adapters**
- **Purpose**: Hardware-specific drivers and communication
- **Key Feature**: Template-based creation, mock variants included
- **Location**: `framework/adapters/`
- **Pattern**: `{name}_adapter.py` with `{Name}Adapter` class

### **Hardware/Mock Layer**
- **Purpose**: Actual devices or simulation
- **Key Feature**: Seamless switching between real/mock hardware
- **Control**: `HARDWARE_PLATFORM` environment variable

## Adding New Hardware Interfaces (Simplified!)

### ✨ **New 3-Step Process** (was 5 steps):

### 1. **Copy & Customize Template**
```bash
# Copy adapter template
cp framework/templates/adapter_template.py framework/adapters/ethernet_adapter.py

# Edit file - replace placeholders:
# {{ADAPTER_NAME}} → Ethernet
# {{ADAPTER_CLASS}} → EthernetAdapter
# {{adapter_name}} → ethernet
# {{DEVICE_PATH}} → /dev/eth0
# Implement TODO methods
```

### 2. **Add Device Configuration**
```yaml
# config/hardware/your_platform.yaml
interfaces:
  ethernet:  # Framework auto-discovers this!
    device_path: "/dev/eth0"
    speed: "1000"
```

### 3. **Use in Tests**
```python
@auto_configure_test
def test_ethernet_feature(ethernet_interface):  # Auto-fixture!
    """Framework automatically provides ethernet_interface"""
    result = ethernet_interface.initialize()
    assert result.success

    result = ethernet_interface.send_packet(b"test")
    assert result.success
```

**That's it!** No HAL editing, no fixture creation - everything is auto-discovered.

### 🔧 **Auto-Discovery Features**

✅ **Adapter Discovery**: Place `*_adapter.py` in `framework/adapters/`
✅ **Interface Access**: `hardware.{name}_interface` automatically works
✅ **Test Fixtures**: `{name}_interface` parameters automatically provided
✅ **Mock Support**: `Mock{Name}Adapter` classes automatically used on mock platform
✅ **Configuration**: Standard YAML config in `config/hardware/`

### 📚 **Templates Available**

- **`framework/templates/adapter_template.py`** - Complete adapter implementation
- **`framework/templates/test_template.py`** - Comprehensive test suite
- **`framework/templates/config_template.yaml`** - Configuration examples
- **`framework/templates/README.md`** - Detailed template usage guide

## Extending Framework Core

### Adding New Test Categories

**Update `config/test_registry.yaml`:**
```yaml
categories:
  your_category:
    description: "Your custom test category"
    max_duration: "15m"
```

### Adding New Platform Support

**Create `config/hardware/your_new_platform.yaml`:**
```yaml
platform:
  name: "Your New Platform"
  version: "1.0"

interfaces:
  can:
    type: "your_can_type"
    custom_config: "value"
```

## Documentation

For additional examples:
- Check `tests/suites/` for test patterns
- Review `config/test_registry.yaml` for configuration examples
- Examine `config/hardware/` for platform configurations
- See `framework/core/` for framework implementation details

## License

MIT License
