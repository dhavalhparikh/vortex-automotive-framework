"""
Configuration Loader Module

Loads and validates hardware configuration files.
Provides a centralized way to access test configuration.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator


class PlatformConfig(BaseModel):
    """Platform metadata"""
    name: str
    version: str
    vendor: str
    description: str = ""


class InterfaceConfig(BaseModel):
    """Base interface configuration"""
    type: str
    
    class Config:
        extra = "allow"  # Allow additional fields


class CANConfig(InterfaceConfig):
    """CAN interface configuration"""
    channel: str
    bitrate: int
    fd_enabled: bool = False
    data_bitrate: Optional[int] = None


class SerialConfig(InterfaceConfig):
    """Serial/UART interface configuration"""
    port: str
    baudrate: int = 115200
    timeout: float = 1.0
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1


class TestParameters(BaseModel):
    """Test execution parameters"""
    default_timeout: float = 5.0
    long_timeout: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    log_level: str = "INFO"


class HardwareConfig(BaseModel):
    """Complete hardware configuration"""
    platform: PlatformConfig
    interfaces: Dict[str, Dict[str, Any]]
    sensors: Optional[Dict[str, Dict[str, Any]]] = None
    diagnostics: Optional[Dict[str, Any]] = None
    test_parameters: TestParameters
    power: Optional[Dict[str, Any]] = None
    calibration: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, Any]] = None
    notes: str = ""
    
    class Config:
        extra = "allow"


class ConfigLoader:
    """
    Loads and manages hardware configurations.
    
    Usage:
        config = ConfigLoader()
        hw_config = config.load_hardware_config("ecu_platform_a")
        can_config = config.get_interface_config("can")
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_dir: Path to configuration directory.
                       Defaults to <project_root>/config
        """
        if config_dir is None:
            # Determine config directory relative to this file
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.hardware_dir = self.config_dir / "hardware"
        self._current_config: Optional[HardwareConfig] = None
        self._platform_name: Optional[str] = None
    
    def load_hardware_config(self, platform_name: Optional[str] = None) -> HardwareConfig:
        """
        Load hardware configuration for specified platform.
        
        Args:
            platform_name: Name of the platform (without .yaml extension).
                          If None, uses HARDWARE_PLATFORM environment variable.
                          Defaults to 'ecu_platform_a' if not specified.
        
        Returns:
            HardwareConfig object with validated configuration
        
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        # Determine platform name
        if platform_name is None:
            platform_name = os.getenv('HARDWARE_PLATFORM', 'ecu_platform_a')
        
        self._platform_name = platform_name
        
        # Build config file path
        config_file = self.hardware_dir / f"{platform_name}.yaml"
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Hardware configuration not found: {config_file}\n"
                f"Available configurations: {self.list_available_platforms()}"
            )
        
        # Load YAML file
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in {config_file}: {e}")
        except IOError as e:
            raise FileNotFoundError(f"Could not read configuration file {config_file}: {e}")

        if config_data is None:
            raise ValueError(f"Configuration file {config_file} is empty or contains only comments")

        # Validate and create config object
        try:
            self._current_config = HardwareConfig(**config_data)
            return self._current_config
        except Exception as e:
            raise ValueError(f"Invalid configuration in {config_file}: {e}")
    
    def get_current_config(self) -> HardwareConfig:
        """
        Get currently loaded configuration.
        
        Returns:
            Current HardwareConfig
        
        Raises:
            RuntimeError: If no configuration is loaded
        """
        if self._current_config is None:
            raise RuntimeError("No configuration loaded. Call load_hardware_config() first.")
        return self._current_config
    
    def get_interface_config(self, interface_name: str) -> Dict[str, Any]:
        """
        Get configuration for specific interface.
        
        Args:
            interface_name: Name of the interface (e.g., 'can', 'serial')
        
        Returns:
            Interface configuration dictionary
        
        Raises:
            KeyError: If interface doesn't exist in configuration
        """
        config = self.get_current_config()
        
        if interface_name not in config.interfaces:
            raise KeyError(
                f"Interface '{interface_name}' not found in configuration. "
                f"Available interfaces: {list(config.interfaces.keys())}"
            )
        
        return config.interfaces[interface_name]
    
    def get_sensor_config(self, sensor_name: str) -> Dict[str, Any]:
        """
        Get configuration for specific sensor.
        
        Args:
            sensor_name: Name of the sensor
        
        Returns:
            Sensor configuration dictionary
        """
        config = self.get_current_config()
        
        if config.sensors is None or sensor_name not in config.sensors:
            raise KeyError(f"Sensor '{sensor_name}' not found in configuration")
        
        return config.sensors[sensor_name]
    
    def get_test_parameters(self) -> TestParameters:
        """Get test execution parameters."""
        return self.get_current_config().test_parameters
    
    def list_available_platforms(self) -> list[str]:
        """
        List all available hardware platform configurations.
        
        Returns:
            List of platform names (without .yaml extension)
        """
        if not self.hardware_dir.exists():
            return []
        
        yaml_files = self.hardware_dir.glob("*.yaml")
        return [f.stem for f in yaml_files]
    
    def get_platform_name(self) -> str:
        """Get name of currently loaded platform."""
        if self._platform_name is None:
            raise RuntimeError("No configuration loaded")
        return self._platform_name
    
    def is_mock_platform(self) -> bool:
        """Check if current platform is a mock/simulated platform."""
        config = self.get_current_config()
        return "mock" in config.platform.name.lower()


# Global singleton instance
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """
    Get global ConfigLoader instance (singleton).
    
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def load_config(platform_name: Optional[str] = None) -> HardwareConfig:
    """
    Convenience function to load hardware configuration.
    
    Args:
        platform_name: Platform name or None for default
    
    Returns:
        Loaded HardwareConfig
    """
    loader = get_config_loader()
    return loader.load_hardware_config(platform_name)
