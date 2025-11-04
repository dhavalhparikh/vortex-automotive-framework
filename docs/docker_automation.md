# Automatic Docker Device Mapping

## Problem Solved

Previously, users had to manually specify `--device` mappings for every hardware device:

```bash
# ❌ Old way - manual and error-prone
docker run --device=/dev/ttyUSB8:/dev/ttyUSB8 --device=/dev/can0:/dev/can0 automotive-tests
```

## Automatic Solution

The framework now **automatically discovers** required hardware devices from your platform configuration and maps them to Docker containers.

## Usage

### Simple Auto-Testing (Recommended)

```bash
# ✅ New way - automatic device discovery with execution profiles
./auto_test.sh my_custom_platform --exec-profile smoke
./auto_test.sh my_custom_platform --exec-profile hil

# Traditional usage still supported
./auto_test.sh my_custom_platform -m smoke
./auto_test.sh my_custom_platform tests/suites/cli_tests/
```

### Advanced Usage

```bash
# Direct auto-mapping with execution profiles
python scripts/auto_docker.py run --platform my_platform --exec-profile smoke
python scripts/auto_docker.py run --platform my_platform --exec-profile hil

# Traditional direct auto-mapping
python scripts/auto_docker.py run --platform my_platform -m smoke

# Generate docker-compose override file
python scripts/auto_docker.py compose --platform my_platform
docker-compose up
```

## How It Works

1. **Platform Analysis**: Reads your platform YAML configuration
2. **Device Discovery**: Extracts device paths from interface configurations
3. **Automatic Mapping**: Maps only the devices you actually use
4. **Smart Filtering**: Skips mock interfaces and missing devices

## Example

**Platform Config** (`config/hardware/my_platform.yaml`):
```yaml
interfaces:
  cli:
    device_path: "/dev/ttyUSB8"  # ← Automatically discovered
    baudrate: 115200

  can:
    type: "mock"  # ← Skipped (no device mapping needed)
```

**Generated Docker Command** (with execution profile):
```bash
docker run --device=/dev/ttyUSB8:/dev/ttyUSB8 \
  -e HARDWARE_PLATFORM=my_platform \
  automotive-tests --exec-profile smoke
```

**Generated Docker Command** (traditional):
```bash
docker run --device=/dev/ttyUSB8:/dev/ttyUSB8 \
  -e HARDWARE_PLATFORM=my_platform \
  automotive-tests -m smoke
```

## Interface to Device Mapping

| Interface | Config Key | Example |
|-----------|------------|---------|
| CLI | `device_path` | `/dev/ttyUSB8` |
| Serial | `port` or `device_path` | `/dev/ttyUSB0` |
| CAN | `channel` | `/dev/can0` |
| SPI | `device_path` | `/dev/spidev0.0` |
| I2C | `device_path` | `/dev/i2c-1` |

## Benefits

- ✅ **No manual device mapping** required
- ✅ **Platform-aware** device discovery
- ✅ **Error prevention** - no typos in device paths
- ✅ **Flexibility** - works with any platform configuration
- ✅ **Development friendly** - automatically skips missing devices
- ✅ **CI/CD ready** - handles mock platforms gracefully

## Migration Guide

### Before (Manual)
```bash
docker run --device=/dev/ttyUSB8:/dev/ttyUSB8 automotive-tests -m smoke
```

### After (Automatic)
```bash
# With execution profiles (recommended)
./auto_test.sh my_platform --exec-profile smoke

# Traditional usage
./auto_test.sh my_platform -m smoke
```

That's it! The framework handles everything automatically based on your platform configuration.