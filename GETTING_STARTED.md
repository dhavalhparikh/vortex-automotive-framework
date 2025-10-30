# Getting Started Guide

## Quick Setup (5 minutes)

### Option 1: Using Docker (Recommended)

```bash
# 1. Clone/Download the framework
# cd project_vortex (already in project root)

# 2. Build container
docker build -t automotive-tests .

# 3. Run smoke tests (with mock hardware)
docker run --rm \
  -e HARDWARE_PLATFORM=mock_platform \
  -v $(pwd)/reports:/app/reports \
  automotive-tests -m smoke

# 4. View reports
cd reports && python -m http.server 8000
# Open: http://localhost:8000/report.html
```

### Option 2: Local Development

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run tests
HARDWARE_PLATFORM=mock_platform pytest -m smoke

# 4. Generate and view Allure report
pytest --alluredir=reports/allure-results
allure serve reports/allure-results
```

## Running Tests with Real Hardware

### 1. Setup Hardware Access

**Linux CAN Interface:**
```bash
# Bring up CAN interface
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up

# Verify
ip -details link show can0
```

**Serial Port:**
```bash
# Check device
ls -l /dev/ttyUSB0

# Add user to dialout group (one-time setup)
sudo usermod -a -G dialout $USER
# Logout and login again

# Or temporarily set permissions
sudo chmod 666 /dev/ttyUSB0
```

### 2. Run Tests with Hardware

**With Docker:**
```bash
docker run --rm \
  --device=/dev/can0:/dev/can0 \
  --device=/dev/ttyUSB0:/dev/ttyUSB0 \
  --cap-add=NET_ADMIN \
  -e HARDWARE_PLATFORM=ecu_platform_a \
  -v $(pwd)/reports:/app/reports \
  automotive-tests -m smoke
```

**Local:**
```bash
HARDWARE_PLATFORM=ecu_platform_a pytest -m smoke
```

## Your First Test

### 1. Create a Test File

Create `tests/suites/my_tests/test_example.py`:

```python
import pytest
import allure

@allure.feature('My Feature')
@pytest.mark.smoke
def test_my_first_test(hardware):
    """My first test"""
    
    # Check platform is initialized
    assert hardware.is_initialized()
    
    # Get platform info
    info = hardware.get_platform_info()
    print(f"Testing on: {info['name']}")
    
    # Test passes!
    assert True
```

### 2. Run Your Test

```bash
pytest tests/suites/my_tests/test_example.py -v
```

## Common Test Patterns

### Testing CAN Communication

```python
@pytest.mark.can_bus
@pytest.mark.smoke
def test_can_send_receive(can_interface):
    """Test CAN message exchange"""
    
    # Send message
    result = can_interface.send_message(0x123, [0x01, 0x02, 0x03])
    assert result.success, f"Send failed: {result.error}"
    
    # Receive message (with mock adapter)
    msg = can_interface.receive_message(timeout=1.0)
    assert msg is not None, "No message received"
    
    print(f"Received ID: 0x{msg.arbitration_id:X}")
```

### Using Test Dependencies

```python
@pytest.mark.dependency(name="test_init")
def test_initialize_system(hardware):
    """Must run first"""
    assert hardware.can.is_ready()

@pytest.mark.dependency(depends=["test_init"])
def test_use_system(hardware):
    """Runs after test_init"""
    hardware.can.send_message(0x100, [0x01])
```

### Parameterized Tests

```python
@pytest.mark.parametrize("msg_id,data", [
    (0x100, [0x01, 0x02]),
    (0x200, [0xAA, 0xBB]),
    (0x300, [0xFF, 0xFF]),
])
def test_various_messages(can_interface, msg_id, data):
    """Test multiple message configurations"""
    result = can_interface.send_message(msg_id, data)
    assert result.success
```

### Enhanced Allure Reporting

```python
import allure
from allure import attachment_type

@allure.feature('CAN Bus')
@allure.story('Diagnostics')
@allure.title("Test UDS diagnostic session")
@allure.severity(allure.severity_level.CRITICAL)
def test_diagnostic_session(can_interface):
    """Test diagnostic session"""
    
    with allure.step("Enter diagnostic session"):
        result = can_interface.send_message(0x7E0, [0x10, 0x01])
        allure.attach(
            f"Request: {result.log}",
            name="Diagnostic Request",
            attachment_type=attachment_type.TEXT
        )
        assert result.success
    
    with allure.step("Receive positive response"):
        response = can_interface.receive_message(timeout=2.0)
        assert response is not None
        assert response.data[0] == 0x50  # Positive response
```

## Running Different Test Suites

```bash
# All smoke tests
pytest -m smoke

# All CAN bus tests
pytest -m can_bus

# Smoke tests for CAN bus only
pytest -m "smoke and can_bus"

# Everything except slow tests
pytest -m "not slow"

# Specific test suite directory
pytest tests/suites/can_bus/

# With coverage
pytest --cov=framework --cov-report=html

# Parallel execution
pytest -n auto -m regression

# Stop on first failure
pytest -x -m smoke

# Collect tests without running
pytest --collect-only
```

## Creating Hardware Configurations

### 1. Create Config File

Create `config/hardware/my_platform.yaml`:

```yaml
platform:
  name: "My ECU Platform"
  version: "1.0"
  vendor: "My Company"

interfaces:
  can:
    type: "socketcan"
    channel: "can0"
    bitrate: 500000
    
  serial:
    type: "uart"
    port: "/dev/ttyUSB0"
    baudrate: 115200

test_parameters:
  default_timeout: 5.0
  retry_count: 3
  log_level: "INFO"
```

### 2. Use Your Configuration

```bash
HARDWARE_PLATFORM=my_platform pytest -m smoke
```

## Troubleshooting

### Tests Not Found

```bash
# Verify test discovery
pytest --collect-only

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### CAN Interface Issues

```bash
# Check interface is up
ip link show can0

# Check for errors
candump can0

# Reset interface
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up
```

### Permission Denied for Devices

```bash
# Temporary fix
sudo chmod 666 /dev/can0
sudo chmod 666 /dev/ttyUSB0

# Permanent fix - add user to groups
sudo usermod -a -G dialout $USER
sudo usermod -a -G can $USER
```

### Docker Cannot Access Devices

```bash
# Ensure devices exist on host
ls -l /dev/can0 /dev/ttyUSB0

# Run with correct device mapping
docker run --rm \
  --device=/dev/can0:/dev/can0 \
  --cap-add=NET_ADMIN \
  automotive-tests
```

### Allure Report Not Generating

```bash
# Install Allure CLI
# macOS
brew install allure

# Linux (manual)
wget https://github.com/allure-framework/allure2/releases/download/2.24.0/allure-2.24.0.tgz
tar -zxvf allure-2.24.0.tgz
sudo mv allure-2.24.0 /opt/allure
export PATH=$PATH:/opt/allure/bin

# Verify installation
allure --version

# Generate report
allure serve reports/allure-results
```

## Next Steps

1. **Add More Tests**: Create test files in `tests/suites/`
2. **Configure Hardware**: Add your platform in `config/hardware/`
3. **Setup CI/CD**: Use examples in `ci/` directory
4. **Customize Markers**: Add project-specific markers in `config/pytest.ini`
5. **Integrate Tools**: Add diagnostic libraries, custom adapters

## Useful Commands

```bash
# List all markers
pytest --markers

# List all fixtures
pytest --fixtures

# Show test durations
pytest --durations=10

# Run last failed tests
pytest --lf

# Debug with pdb
pytest --pdb

# Update snapshots (if using)
pytest --snapshot-update

# Generate coverage badge
pytest --cov=framework --cov-report=term
```

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [Allure documentation](https://docs.qameta.io/allure/)
- [python-can documentation](https://python-can.readthedocs.io/)
- [Docker documentation](https://docs.docker.com/)

## Getting Help

- Check `README.md` for overview
- Review example tests in `tests/suites/`
- Examine hardware configs in `config/hardware/`
- Look at CI/CD examples in `ci/`
