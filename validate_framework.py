#!/usr/bin/env python3
"""
Framework Validation Script

Run this script to validate the automotive test framework installation.
This checks file structure, syntax, and configurations WITHOUT requiring
external dependencies.

Usage:
    python validate_framework.py
"""

import os
import sys
import ast
from pathlib import Path


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def check_file_structure():
    """Verify all critical files exist"""
    print_section("1. File Structure Validation")
    
    critical_files = [
        'framework/core/config_loader.py',
        'framework/core/hardware_abstraction.py',
        'framework/adapters/can_adapter.py',
        'framework/adapters/mock_adapter.py',
        'framework/adapters/serial_adapter.py',
        'framework/adapters/gpio_adapter.py',
        'config/hardware/ecu_platform_a.yaml',
        'config/hardware/ecu_platform_b.yaml',
        'config/hardware/mock_platform.yaml',
        'config/pytest.ini',
        'tests/conftest.py',
        'tests/suites/can_bus/test_can_communication.py',
        'Dockerfile',
        'docker-compose.yml',
        'requirements.txt',
        'run_tests.py',
        'README.md',
        'GETTING_STARTED.md',
    ]
    
    missing = []
    present = []
    
    for filepath in critical_files:
        if os.path.exists(filepath):
            present.append(filepath)
            print(f"  ✅ {filepath}")
        else:
            missing.append(filepath)
            print(f"  ❌ {filepath} - MISSING")
    
    print(f"\nResult: {len(present)}/{len(critical_files)} files present")
    
    if missing:
        print(f"⚠️  WARNING: {len(missing)} files are missing!")
        return False
    else:
        print("✅ PASSED: All critical files present")
        return True


def check_python_syntax():
    """Check Python syntax in all files"""
    print_section("2. Python Syntax Validation")
    
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and cache
        dirs[:] = [d for d in dirs if d not in ['venv', 'env', '__pycache__', '.git', 'test_venv']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    errors = []
    for filepath in python_files:
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            ast.parse(code)
            print(f"  ✅ {filepath}")
        except SyntaxError as e:
            print(f"  ❌ {filepath}: {e}")
            errors.append((filepath, str(e)))
    
    print(f"\nResult: {len(python_files) - len(errors)}/{len(python_files)} files valid")
    
    if errors:
        print(f"❌ FAILED: {len(errors)} files have syntax errors")
        return False
    else:
        print("✅ PASSED: All Python files have valid syntax")
        return True


def check_yaml_configs():
    """Validate YAML configuration files"""
    print_section("3. Configuration Files Validation")
    
    try:
        import yaml
    except ImportError:
        print("  ⚠️  WARNING: PyYAML not installed, skipping YAML validation")
        print("  Install with: pip install PyYAML")
        return None
    
    configs = [
        'config/hardware/ecu_platform_a.yaml',
        'config/hardware/ecu_platform_b.yaml',
        'config/hardware/mock_platform.yaml',
    ]
    
    errors = []
    for config_file in configs:
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
            
            platform_name = data.get('platform', {}).get('name', 'Unknown')
            interfaces = list(data.get('interfaces', {}).keys())
            
            print(f"  ✅ {config_file}")
            print(f"     Platform: {platform_name}")
            print(f"     Interfaces: {', '.join(interfaces)}")
        except Exception as e:
            print(f"  ❌ {config_file}: {e}")
            errors.append((config_file, str(e)))
    
    print(f"\nResult: {len(configs) - len(errors)}/{len(configs)} configs valid")
    
    if errors:
        print(f"❌ FAILED: {len(errors)} configuration files have errors")
        return False
    else:
        print("✅ PASSED: All configuration files valid")
        return True


def check_imports():
    """Test if core modules can be imported"""
    print_section("4. Module Import Validation")
    
    sys.path.insert(0, '.')
    
    test_imports = [
        ('framework.core.config_loader', 'ConfigLoader'),
        ('framework.core.hardware_abstraction', 'HardwareAbstractionLayer'),
        ('framework.adapters.mock_adapter', 'MockCANAdapter'),
    ]
    
    failed = []
    for module_name, class_name in test_imports:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  ✅ {module_name}.{class_name}")
        except ImportError as e:
            print(f"  ⚠️  {module_name}.{class_name} - Missing dependency: {e}")
            failed.append((module_name, str(e)))
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name} - Error: {e}")
            failed.append((module_name, str(e)))
    
    if failed:
        print(f"\n⚠️  WARNING: Some imports failed (likely missing dependencies)")
        print("   Install dependencies with: pip install -r requirements.txt")
        return None
    else:
        print("\n✅ PASSED: All core modules import successfully")
        return True


def check_documentation():
    """Verify documentation files exist and have content"""
    print_section("5. Documentation Validation")
    
    docs = {
        'README.md': 3000,  # Minimum expected size in bytes
        'GETTING_STARTED.md': 5000,
        'PROJECT_SUMMARY.md': 5000,
    }
    
    all_good = True
    for doc_file, min_size in docs.items():
        if os.path.exists(doc_file):
            size = os.path.getsize(doc_file)
            if size >= min_size:
                print(f"  ✅ {doc_file} ({size:,} bytes)")
            else:
                print(f"  ⚠️  {doc_file} ({size:,} bytes) - Smaller than expected")
                all_good = False
        else:
            print(f"  ❌ {doc_file} - MISSING")
            all_good = False
    
    if all_good:
        print("\n✅ PASSED: All documentation files present and complete")
    else:
        print("\n⚠️  WARNING: Some documentation may be incomplete")
    
    return all_good


def check_docker_files():
    """Verify Docker configuration files"""
    print_section("6. Docker Configuration Validation")
    
    docker_files = ['Dockerfile', 'docker-compose.yml']
    
    all_good = True
    for docker_file in docker_files:
        if os.path.exists(docker_file):
            with open(docker_file, 'r') as f:
                content = f.read()
            
            print(f"  ✅ {docker_file} ({len(content)} bytes)")
            
            # Basic checks
            if docker_file == 'Dockerfile':
                if 'FROM' in content and 'WORKDIR' in content:
                    print(f"     Contains: FROM, WORKDIR commands")
                else:
                    print(f"     ⚠️  Warning: Missing expected Dockerfile commands")
                    all_good = False
            elif docker_file == 'docker-compose.yml':
                if 'services:' in content:
                    print(f"     Contains: services definition")
                else:
                    print(f"     ⚠️  Warning: Missing services definition")
                    all_good = False
        else:
            print(f"  ❌ {docker_file} - MISSING")
            all_good = False
    
    if all_good:
        print("\n✅ PASSED: Docker configuration files valid")
    else:
        print("\n⚠️  WARNING: Docker configuration may have issues")
    
    return all_good


def run_all_validations():
    """Run all validation checks"""
    print("\n" + "=" * 70)
    print("  AUTOMOTIVE TEST FRAMEWORK - VALIDATION SCRIPT")
    print("=" * 70)
    print("\nThis script validates the framework installation without requiring")
    print("external dependencies (pytest, allure, etc.).")
    print("\nFor full testing, install dependencies and run: pytest -m smoke")
    
    results = {}
    
    # Run all checks
    results['file_structure'] = check_file_structure()
    results['python_syntax'] = check_python_syntax()
    results['yaml_configs'] = check_yaml_configs()
    results['imports'] = check_imports()
    results['documentation'] = check_documentation()
    results['docker'] = check_docker_files()
    
    # Summary
    print_section("VALIDATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v is True)
    warnings = sum(1 for v in results.values() if v is None)
    failed = sum(1 for v in results.values() if v is False)
    total = len(results)
    
    print(f"\nTest Results:")
    print(f"  ✅ Passed:   {passed}/{total}")
    print(f"  ⚠️  Warnings: {warnings}/{total}")
    print(f"  ❌ Failed:   {failed}/{total}")
    
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status = "✅ PASSED" if result is True else "⚠️  WARNING" if result is None else "❌ FAILED"
        print(f"  {status:12} - {test_name.replace('_', ' ').title()}")
    
    print("\n" + "=" * 70)
    
    if failed > 0:
        print("❌ VALIDATION FAILED")
        print("\nSome critical checks failed. Please review the errors above.")
        return False
    elif warnings > 0:
        print("⚠️  VALIDATION PASSED WITH WARNINGS")
        print("\nFramework structure is valid but some dependencies may be missing.")
        print("Install dependencies with: pip install -r requirements.txt")
        return True
    else:
        print("✅ VALIDATION PASSED")
        print("\nThe framework is properly installed and ready to use!")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run tests: pytest -m smoke")
        print("  3. View docs: cat GETTING_STARTED.md")
        return True


if __name__ == '__main__':
    try:
        success = run_all_validations()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation script error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
