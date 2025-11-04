# Execution Profiles

## Overview

Execution profiles provide a powerful way to organize and run different sets of tests for different scenarios like smoke testing, HIL testing, nightly runs, and more. They separate **test definition** (what tests exist) from **test execution** (which tests to run when).

## Architecture

The test registry is now split into three main components:

```
config/test_registry/
├── suites/              # Test definitions organized by functionality
│   ├── can_bus.yaml
│   ├── cli_tests.yaml
│   ├── spi_tests.yaml
│   └── diagnostics.yaml
├── execution/           # Execution profiles for different test benches
│   ├── smoke.yaml
│   ├── regression.yaml
│   ├── hil.yaml
│   └── nightly.yaml
└── _globals.yaml        # Shared categories, priorities, defaults
```

## Benefits

✅ **No Test Duplication** - Tests defined once, used in multiple profiles
✅ **Flexible Execution** - Different test benches run different test sets
✅ **Metadata Overrides** - Customize test behavior per execution context
✅ **Maintainable** - Small, focused files instead of monolithic registry
✅ **Backward Compatible** - Existing CLI commands still work

## Test Suite Structure

Test suites define the actual tests organized by functionality:

```yaml
# config/test_registry/suites/can_bus.yaml
suite_info:
  name: "can_bus"
  description: "CAN bus communication tests"
  default_platforms: ["ecu_platform_a", "ecu_platform_b", "mock_platform"]

tests:
  - name: "test_can_initialization"
    category: "smoke"
    priority: "critical"
    description: "Test CAN interface initialization"
    platforms: ["all"]

  - name: "test_can_cleanup"
    category: "smoke"
    priority: "critical"
    description: "Test CAN interface cleanup"
    platforms: ["all"]
```

## Execution Profile Structure

Execution profiles define which tests to run for specific scenarios:

```yaml
# config/test_registry/execution/smoke.yaml
execution_profile:
  name: "smoke"
  description: "Critical smoke tests for fast feedback"
  timeout: 300

include:
  # Include entire suites
  - suite: "mock_adapter"

  # Include specific tests with overrides
  - suite: "can_bus"
    tests: ["test_can_initialization", "test_can_cleanup"]
    overrides:
      timeout: 60
      priority: "critical"
      platforms: ["mock_platform"]  # Force mock for smoke tests

  # Include suite with global overrides
  - suite: "cli_tests"
    overrides:
      requirements_hardware: false
```

## Execution Profile Features

### **Flexible Test Inclusion**

Include entire suites or specific tests:

```yaml
include:
  # Entire suite
  - suite: "can_bus"

  # Specific tests only
  - suite: "diagnostics"
    tests: ["test_uds_session_control", "test_diagnostic_read"]
```

### **Metadata Overrides**

Customize test behavior per execution context:

```yaml
include:
  - suite: "can_bus"
    overrides:
      platforms: ["mock_platform"]      # Override platforms
      timeout: 30                       # Override timeout
      priority: "critical"              # Elevate priority
      requirements_hardware: false     # Force mock mode
      category: "smoke"                 # Change category
```

### **Profile-Level Configuration**

Set profile-wide defaults:

```yaml
execution_profile:
  name: "hil"
  description: "Hardware-in-the-loop testing"
  timeout: 1800                        # 30 minute timeout for HIL

include:
  - suite: "can_bus"
    # All tests inherit 30 minute timeout unless overridden
```

## Usage Examples

### **List Available Profiles**

```bash
python run_tests.py --list-profiles
```

Output:
```
Available execution profiles:
  integration: Integration and cross-component tests
  nightly: Comprehensive nightly test run
  regression: Full regression test suite
  smoke: Critical smoke tests for fast feedback

Usage:
  python run_tests.py --exec-profile smoke
  python run_tests.py --exec-profile hil --platform ecu_platform_a
```

### **Run Execution Profiles**

```bash
# Run all tests from smoke profile
python run_tests.py --exec-profile smoke

# Run smoke tests on specific platform
python run_tests.py --exec-profile hil --platform ecu_platform_a

# Run and generate Allure report
python run_tests.py --exec-profile nightly --allure
```

### **Filter Tests Within Profiles**

```bash
# Run only CAN tests from smoke profile
python run_tests.py --exec-profile smoke --suite can_bus

# Run only critical tests from regression profile
python run_tests.py --exec-profile regression --priority critical

# Run specific tests from a profile
python run_tests.py --exec-profile smoke test_can_initialization
```

### **Docker Integration**

```bash
# Auto device mapping with execution profiles
./auto_test.sh custom_platform --exec-profile smoke
./auto_test.sh hil_platform --exec-profile hil
```

## Backward Compatibility

All existing commands continue to work:

```bash
# Traditional usage still supported
python run_tests.py -m smoke
python run_tests.py --suite can_bus
python run_tests.py --category regression
```

The framework automatically detects whether to use split registry or legacy format.

## Migration

### **Automatic Migration**

Migrate from monolithic `test_registry.yaml`:

```bash
python scripts/migrate_registry.py
```

This creates:
- Split test suite files in `suites/`
- Execution profiles in `execution/`
- Global configuration in `_globals.yaml`
- Backup of original file

### **Manual Creation**

Create new execution profiles manually:

```bash
# Create new execution profile
touch config/test_registry/execution/performance.yaml
```

Example performance profile:
```yaml
execution_profile:
  name: "performance"
  description: "Performance and load testing"
  timeout: 3600

include:
  - suite: "can_bus"
    tests: ["test_can_throughput", "test_can_stress"]
  - suite: "network"
    overrides:
      category: "performance"
```

## Best Practices

### **Test Suite Organization**

✅ **Group by functionality** - CAN tests together, CLI tests together
✅ **Keep suites focused** - Each suite should have a clear purpose
✅ **Use descriptive names** - `diagnostics.yaml` not `test_group_1.yaml`

### **Execution Profile Design**

✅ **Profile per test bench** - `smoke.yaml`, `hil.yaml`, `nightly.yaml`
✅ **Meaningful overrides** - Override platforms, timeouts, priorities appropriately
✅ **Documentation** - Include clear descriptions for each profile

### **Metadata Consistency**

✅ **Use global defaults** - Set common values in `_globals.yaml`
✅ **Validate regularly** - Run migration validation after changes
✅ **Review overrides** - Ensure profile overrides make sense

## Advanced Features

### **Hierarchical Overrides**

Override precedence (highest to lowest):
1. CLI arguments (`--platform`, `--priority`)
2. Execution profile overrides
3. Suite defaults
4. Global defaults

### **Profile Composition**

Create complex profiles by including multiple suites with different configurations:

```yaml
execution_profile:
  name: "comprehensive"
  description: "Full test coverage across all domains"

include:
  # Critical tests with short timeout
  - suite: "can_bus"
    tests: ["test_can_initialization"]
    overrides:
      timeout: 30
      priority: "critical"

  # Full regression with normal timeout
  - suite: "diagnostics"
    overrides:
      timeout: 300

  # Performance tests with extended timeout
  - suite: "network"
    tests: ["test_throughput"]
    overrides:
      timeout: 1800
      category: "performance"
```

### **Platform-Specific Profiles**

```yaml
# execution/hil_platform_a.yaml
execution_profile:
  name: "hil_platform_a"
  description: "HIL testing specific to Platform A hardware"

include:
  - suite: "can_bus"
    overrides:
      platforms: ["ecu_platform_a"]
      requirements_hardware: true

  - suite: "gpio"
    tests: ["test_platform_a_gpio"]
    overrides:
      platforms: ["ecu_platform_a"]
```

## Troubleshooting

### **Profile Not Found**

```bash
Error: Execution profile 'hil' not found.
Available profiles: smoke, regression, integration, nightly
```

**Solution**: Check profile exists in `config/test_registry/execution/` or run `--list-profiles`

### **No Tests in Profile**

```bash
Warning: Execution profile 'empty' contains no tests.
```

**Solution**: Check `include` section has valid suite references and test names

### **Migration Issues**

```bash
python scripts/migrate_registry.py --validate-only
```

**Solution**: Validates migration completed successfully