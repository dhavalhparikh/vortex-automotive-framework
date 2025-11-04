#!/usr/bin/env python3
"""
Debug script to check configuration loading
"""
import os
from framework.core.config_loader import load_config

def debug_config():
    print(f"HARDWARE_PLATFORM environment: {os.getenv('HARDWARE_PLATFORM', 'NOT SET')}")

    try:
        config = load_config()
        print(f"Loaded platform: {config.platform.name}")
        print(f"CLI config: {config.interfaces.get('cli', 'NOT FOUND')}")

        if 'cli' in config.interfaces:
            cli_config = config.interfaces['cli']
            print(f"  device_path: {cli_config.get('device_path', 'NOT SET')}")
            print(f"  type: {cli_config.get('type', 'NOT SET')}")

    except Exception as e:
        print(f"Config loading failed: {e}")

if __name__ == "__main__":
    debug_config()