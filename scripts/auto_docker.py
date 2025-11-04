#!/usr/bin/env python3
"""
Automatic Docker Device Mapper

Analyzes platform configuration and automatically maps required hardware devices
to Docker containers. No more manual --device mappings!

Usage:
    python scripts/auto_docker.py run --platform my_platform -m smoke
    python scripts/auto_docker.py compose --platform my_platform
"""

import os
import sys
import yaml
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Set


class AutoDockerMapper:
    """Automatically maps hardware devices to Docker based on platform config"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config" / "hardware"

    def discover_required_devices(self, platform_name: str) -> Set[str]:
        """
        Analyze platform config and discover required device mappings

        Args:
            platform_name: Platform configuration name

        Returns:
            Set of device paths that need to be mapped
        """
        config_file = self.config_dir / f"{platform_name}.yaml"

        if not config_file.exists():
            print(f"❌ Platform config not found: {config_file}")
            available = [f.stem for f in self.config_dir.glob("*.yaml")]
            print(f"Available platforms: {', '.join(available)}")
            sys.exit(1)

        # Load platform configuration
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        required_devices = set()
        interfaces = config.get('interfaces', {})

        for interface_name, interface_config in interfaces.items():
            # Skip mock interfaces
            if interface_config.get('type') == 'mock':
                continue

            # Map interface types to device patterns
            device_path = self._extract_device_path(interface_name, interface_config)
            if device_path:
                required_devices.add(device_path)

        return required_devices

    def _extract_device_path(self, interface_name: str, config: Dict) -> str:
        """Extract device path from interface configuration"""

        # Direct device_path specification
        if 'device_path' in config:
            return config['device_path']

        # Interface-specific device path keys
        device_key_mapping = {
            'cli': 'device_path',
            'serial': 'port',
            'can': 'channel',
            'spi': 'device_path',
            'i2c': 'device_path',
            'gpio': 'device_path'
        }

        key = device_key_mapping.get(interface_name)
        if key and key in config:
            device = config[key]
            # Handle virtual devices
            if device.startswith('vcan') or device == 'mock_serial':
                return None
            return device

        return None

    def check_device_availability(self, devices: Set[str]) -> Dict[str, bool]:
        """Check if required devices exist on the host system"""
        availability = {}

        for device in devices:
            if device and Path(device).exists():
                availability[device] = True
                print(f"✅ Found device: {device}")
            else:
                availability[device] = False
                print(f"⚠️  Device not found: {device}")

        return availability

    def generate_device_mappings(self, devices: Set[str], check_availability: bool = True) -> List[str]:
        """
        Generate Docker device mapping arguments

        Args:
            devices: Set of device paths to map
            check_availability: Whether to check if devices exist

        Returns:
            List of --device arguments for Docker
        """
        device_args = []

        for device in devices:
            if not device:
                continue

            if check_availability and not Path(device).exists():
                print(f"⚠️  Skipping missing device: {device}")
                continue

            # Map device with same path inside container
            device_args.extend(['--device', f'{device}:{device}'])

        return device_args

    def run_docker_with_auto_devices(self, platform_name: str, docker_args: List[str]):
        """Run Docker with automatically discovered device mappings"""
        print(f"🔍 Analyzing platform: {platform_name}")

        # Discover required devices
        required_devices = self.discover_required_devices(platform_name)

        if not required_devices:
            print("📱 No hardware devices required (all mock interfaces)")
        else:
            print(f"📱 Required devices: {', '.join(sorted(required_devices))}")

            # Check device availability
            self.check_device_availability(required_devices)

        # Generate device mappings
        device_mappings = self.generate_device_mappings(required_devices)

        # Build Docker command
        docker_cmd = ['docker', 'run', '--rm']

        # Add automatic device mappings
        docker_cmd.extend(device_mappings)

        # Add environment variables
        docker_cmd.extend([
            '-e', f'HARDWARE_PLATFORM={platform_name}',
            '-e', 'PYTHONPATH=/app',
            '-e', 'PYTHONUNBUFFERED=1'
        ])

        # Add volume mounts
        docker_cmd.extend([
            '-v', f'{self.project_root}/reports:/app/reports',
            '-v', f'{self.project_root}/config:/app/config',
        ])

        # Add network capabilities if needed
        if any('can' in str(d) for d in required_devices):
            docker_cmd.extend(['--cap-add', 'NET_ADMIN', '--network', 'host'])

        # Add Docker image and user arguments
        docker_cmd.append('automotive-tests')  # Assumes image is built
        docker_cmd.extend(docker_args)

        print(f"🐳 Running Docker command:")
        print(f"   {' '.join(docker_cmd)}")
        print()

        # Execute Docker command
        try:
            subprocess.run(docker_cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker command failed with exit code {e.returncode}")
            sys.exit(e.returncode)
        except FileNotFoundError:
            print("❌ Docker not found. Please install Docker.")
            sys.exit(1)

    def generate_docker_compose_override(self, platform_name: str):
        """Generate docker-compose override with automatic device mappings"""
        print(f"🔍 Generating docker-compose override for platform: {platform_name}")

        # Discover required devices
        required_devices = self.discover_required_devices(platform_name)

        # Generate compose override
        override = {
            'version': '3.8',
            'services': {
                'test-runner': {
                    'environment': {
                        'HARDWARE_PLATFORM': platform_name
                    }
                }
            }
        }

        if required_devices:
            device_list = []
            for device in sorted(required_devices):
                if device and Path(device).exists():
                    device_list.append(f"{device}:{device}")

            if device_list:
                override['services']['test-runner']['devices'] = device_list

        # Write override file
        override_file = self.project_root / "docker-compose.override.yml"
        with open(override_file, 'w') as f:
            yaml.dump(override, f, default_flow_style=False)

        print(f"📝 Generated: {override_file}")
        print(f"   Run with: docker-compose up")

        return override_file


def main():
    parser = argparse.ArgumentParser(
        description="Automatic Docker device mapping for hardware testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run tests with automatic device mapping
    python scripts/auto_docker.py run --platform my_custom_platform -m smoke

    # Generate docker-compose override file
    python scripts/auto_docker.py compose --platform my_custom_platform

    # Run specific test suite
    python scripts/auto_docker.py run --platform my_platform tests/suites/cli_tests/
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Run command
    run_parser = subparsers.add_parser('run', help='Run Docker with auto device mapping')
    run_parser.add_argument('--platform', required=True, help='Platform configuration name')
    run_parser.add_argument('args', nargs='*', help='Arguments to pass to test runner')

    # Compose command
    compose_parser = subparsers.add_parser('compose', help='Generate docker-compose override')
    compose_parser.add_argument('--platform', required=True, help='Platform configuration name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    mapper = AutoDockerMapper()

    if args.command == 'run':
        mapper.run_docker_with_auto_devices(args.platform, args.args)
    elif args.command == 'compose':
        mapper.generate_docker_compose_override(args.platform)


if __name__ == "__main__":
    main()