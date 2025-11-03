#!/usr/bin/env python3
"""
VORTEX Adapter Generator

Automatically generates complete adapter implementations from templates.
This is Phase 2 of the simplified adapter creation process.

Usage:
    python scripts/create_adapter.py cli
    python scripts/create_adapter.py ethernet --device /dev/eth0 --methods "send_packet,receive_packet"
    python scripts/create_adapter.py spi --mock --tests
"""

import argparse
import os
import re
from pathlib import Path
from typing import List, Dict, Any


class AdapterGenerator:
    """Generates adapter files from templates"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.templates_dir = self.project_root / "framework" / "templates"
        self.adapters_dir = self.project_root / "framework" / "adapters"
        self.tests_dir = self.project_root / "tests" / "suites"
        self.config_dir = self.project_root / "config"

    def generate_adapter(self,
                        name: str,
                        device_path: str = None,
                        methods: List[str] = None,
                        description: str = None,
                        with_mock: bool = True,
                        with_tests: bool = False,
                        test_category: str = "regression",
                        test_priority: str = "medium") -> None:
        """
        Generate complete adapter implementation

        Args:
            name: Adapter name (e.g., 'cli', 'ethernet')
            device_path: Default device path
            methods: List of custom methods to generate
            description: Adapter description
            with_mock: Generate mock adapter class
            with_tests: Generate test files
            test_category: Test category for registry
            test_priority: Test priority for registry
        """
        print(f"🚀 Generating {name} adapter...")

        # Calculate names and paths
        names = self._calculate_names(name, device_path, description)

        # Generate adapter file
        self._generate_adapter_file(names, methods, with_mock)

        # Generate test files if requested
        if with_tests:
            self._generate_test_files(names, test_category, test_priority)

        # Generate configuration examples
        self._generate_config_examples(names)

        # Update documentation
        self._update_documentation(names)

        print(f"✅ {names['adapter_class']} generated successfully!")
        print(f"\n📁 Generated files:")
        print(f"   📄 framework/adapters/{names['adapter_name']}_adapter.py")
        if with_tests:
            print(f"   📄 tests/suites/{names['adapter_name']}_tests/test_{names['adapter_name']}.py")
        print(f"   📄 config/examples/{names['adapter_name']}_config.yaml")

        print(f"\n🎯 Next steps:")
        print(f"   1. Edit framework/adapters/{names['adapter_name']}_adapter.py")
        print(f"   2. Implement the TODO methods")
        print(f"   3. Add to your platform config:")
        print(f"      interfaces:")
        print(f"        {names['adapter_name']}:")
        print(f"          device_path: \"{names['device_path']}\"")
        print(f"   4. Use in tests: {names['adapter_name']}_interface")

    def _calculate_names(self, name: str, device_path: str = None, description: str = None) -> Dict[str, str]:
        """Calculate all name variations"""
        adapter_name = name.lower()
        adapter_class = f"{name.title()}Adapter"
        mock_class = f"Mock{adapter_class}"

        # Smart device path guessing
        if not device_path:
            device_path = self._guess_device_path(adapter_name)

        # Smart description generation
        if not description:
            description = f"{name.title()} interface for communication and control"

        return {
            'adapter_name': adapter_name,
            'adapter_class': adapter_class,
            'mock_class': mock_class,
            'name_title': name.title(),
            'device_path': device_path,
            'description': description
        }

    def _guess_device_path(self, adapter_name: str) -> str:
        """Smart device path guessing based on adapter name"""
        path_mapping = {
            'cli': '/dev/ttyUSB0',
            'serial': '/dev/ttyUSB0',
            'uart': '/dev/ttyUSB0',
            'spi': '/dev/spidev0.0',
            'i2c': '/dev/i2c-1',
            'ethernet': '/dev/eth0',
            'can': '/dev/can0',
            'gpio': '/dev/gpiochip0',
            'usb': '/dev/ttyUSB0'
        }
        return path_mapping.get(adapter_name, f'/dev/{adapter_name}0')

    def _generate_adapter_file(self, names: Dict[str, str], methods: List[str] = None, with_mock: bool = True):
        """Generate the main adapter file"""
        template_path = self.templates_dir / "adapter_template.py"
        output_path = self.adapters_dir / f"{names['adapter_name']}_adapter.py"

        # Read template
        with open(template_path, 'r') as f:
            content = f.read()

        # Replace placeholders
        replacements = {
            '{{ADAPTER_NAME}}': names['name_title'],
            '{{ADAPTER_CLASS}}': names['adapter_class'],
            '{{adapter_name}}': names['adapter_name'],
            '{{DEVICE_PATH}}': names['device_path']
        }

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        # Add custom methods if specified
        if methods:
            custom_methods = self._generate_custom_methods(methods, names)
            # Insert before the mock class
            mock_class_start = content.find(f"class Mock{names['adapter_class']}")
            if mock_class_start != -1:
                content = content[:mock_class_start] + custom_methods + "\n\n" + content[mock_class_start:]

        # Write adapter file
        with open(output_path, 'w') as f:
            f.write(content)

        print(f"   ✅ Generated adapter: {output_path}")

    def _generate_custom_methods(self, methods: List[str], names: Dict[str, str]) -> str:
        """Generate custom method implementations"""
        method_template = '''    def {method_name}(self, *args, **kwargs) -> OperationResult:
        """
        {method_description}

        Args:
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            OperationResult: Success/failure with response data
        """
        if not self.is_ready():
            return OperationResult(
                success=False,
                error="{adapter_name} not initialized"
            )

        try:
            # TODO: Implement {method_name} logic

            return OperationResult(
                success=True,
                data="TODO: Implement {method_name}",
                log=f"{adapter_name} {method_name} executed"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to execute {method_name}: {{str(e)}}"
            )

'''

        custom_methods = ""
        for method in methods:
            method_description = f"Custom {method} method for {names['name_title']} adapter"
            custom_methods += method_template.format(
                method_name=method,
                method_description=method_description,
                adapter_name=names['name_title']
            )

        return custom_methods

    def _generate_test_files(self, names: Dict[str, str], category: str, priority: str):
        """Generate test files"""
        test_dir = self.tests_dir / f"{names['adapter_name']}_tests"
        test_dir.mkdir(exist_ok=True)

        template_path = self.templates_dir / "test_template.py"
        output_path = test_dir / f"test_{names['adapter_name']}.py"

        # Read template
        with open(template_path, 'r') as f:
            content = f.read()

        # Replace placeholders
        replacements = {
            '{{ADAPTER_NAME}}': names['name_title'],
            '{{ADAPTER_CLASS}}': names['adapter_class'],
            '{{adapter_name}}': names['adapter_name']
        }

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        # Write test file
        with open(output_path, 'w') as f:
            f.write(content)

        print(f"   ✅ Generated tests: {output_path}")

    def _generate_config_examples(self, names: Dict[str, str]):
        """Generate configuration examples"""
        examples_dir = self.config_dir / "examples"
        examples_dir.mkdir(exist_ok=True)

        template_path = self.templates_dir / "config_template.yaml"
        output_path = examples_dir / f"{names['adapter_name']}_config.yaml"

        # Read template
        with open(template_path, 'r') as f:
            content = f.read()

        # Replace placeholders
        replacements = {
            '{{ADAPTER_NAME}}': names['name_title'],
            '{{adapter_name}}': names['adapter_name'],
            '{{DEVICE_PATH}}': names['device_path'],
            '{{PLATFORM_NAME}}': f"Platform with {names['name_title']}"
        }

        for placeholder, value in replacements.items():
            content = content.replace(placeholder, value)

        # Write config file
        with open(output_path, 'w') as f:
            f.write(content)

        print(f"   ✅ Generated config: {output_path}")

    def _update_documentation(self, names: Dict[str, str]):
        """Update documentation with new adapter info"""
        # This could update README.md or other docs
        # For now, just print info
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Generate VORTEX hardware adapters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Simple adapter
    python scripts/create_adapter.py cli

    # With custom device and methods
    python scripts/create_adapter.py cli --device /dev/ttyUSB0 --methods "execute_command,get_response"

    # With tests and mock
    python scripts/create_adapter.py ethernet --tests --mock --device /dev/eth0

    # Full featured
    python scripts/create_adapter.py gpio --device /dev/gpiochip0 --methods "set_pin,get_pin,configure" --tests --priority high
        """
    )

    parser.add_argument('name', help='Adapter name (e.g., cli, ethernet, spi)')
    parser.add_argument('--device', help='Default device path (auto-guessed if not provided)')
    parser.add_argument('--methods', help='Comma-separated list of custom methods to generate')
    parser.add_argument('--description', help='Adapter description')
    parser.add_argument('--mock', action='store_true', default=True, help='Generate mock adapter (default: true)')
    parser.add_argument('--no-mock', action='store_true', help='Skip mock adapter generation')
    parser.add_argument('--tests', action='store_true', help='Generate test files')
    parser.add_argument('--category', default='regression', help='Test category (default: regression)')
    parser.add_argument('--priority', default='medium', help='Test priority (default: medium)')

    args = parser.parse_args()

    # Parse methods
    methods = []
    if args.methods:
        methods = [m.strip() for m in args.methods.split(',')]

    # Handle mock flags
    with_mock = args.mock and not args.no_mock

    # Create generator and run
    generator = AdapterGenerator()
    generator.generate_adapter(
        name=args.name,
        device_path=args.device,
        methods=methods,
        description=args.description,
        with_mock=with_mock,
        with_tests=args.tests,
        test_category=args.category,
        test_priority=args.priority
    )


if __name__ == "__main__":
    main()