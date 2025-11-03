"""
Hardware Abstraction Layer (HAL)

Provides a unified interface to access different hardware components
regardless of the underlying platform.

Supports auto-discovery of adapters - any *_adapter.py in framework/adapters/
can be accessed via hardware.{name}_interface automatically.
"""

import importlib
import logging
from typing import Optional, Dict, Any, TYPE_CHECKING

from framework.core.config_loader import ConfigLoader, HardwareConfig
from framework.core.types import OperationResult

if TYPE_CHECKING:
    from framework.adapters.can_adapter import CANAdapter
    from framework.adapters.serial_adapter import SerialAdapter
    from framework.adapters.gpio_adapter import GPIOAdapter

logger = logging.getLogger(__name__)


class HardwareAbstractionLayer:
    """
    Main hardware abstraction layer class.
    
    Provides unified access to all hardware interfaces.
    Automatically selects appropriate adapter based on configuration.
    
    Usage:
        hal = HardwareAbstractionLayer()
        hal.initialize()
        
        # Access CAN bus
        result = hal.can.send_message(0x123, [0x01, 0x02])
        if result.success:
            print("Message sent")
        
        # Access serial port
        data = hal.serial.read_line()
        
        # Control GPIO
        hal.gpio.set_pin(17, True)
    """
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None, platform: Optional[str] = None):
        """
        Initialize HAL.

        Args:
            config_loader: ConfigLoader instance. If None, creates new one.
            platform: Hardware platform name. If None, uses environment variable.
        """
        self.config_loader = config_loader or ConfigLoader()
        self.config: HardwareConfig = self.config_loader.load_hardware_config(platform)

        # Interface adapters (legacy - keeping for backward compatibility)
        self._can = None
        self._serial = None
        self._gpio = None

        # Dynamic adapter cache for auto-discovery
        self._dynamic_adapters = {}

        # Initialization state
        self._initialized = False
    
    def initialize(self) -> OperationResult:
        """
        Initialize all hardware interfaces.
        
        Returns:
            OperationResult indicating success/failure
        """
        try:
            # Initialize each interface if configured
            if 'can' in self.config.interfaces:
                self._initialize_can()
            
            if 'serial' in self.config.interfaces:
                self._initialize_serial()
            
            if 'gpio' in self.config.interfaces:
                self._initialize_gpio()
            
            self._initialized = True
            return OperationResult(
                success=True,
                log=f"HAL initialized for platform: {self.config.platform.name}"
            )
        
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"HAL initialization failed: {str(e)}"
            )
    
    def _initialize_can(self):
        """Initialize CAN interface"""
        from framework.adapters.can_adapter import CANAdapter
        from framework.adapters.mock_adapter import MockCANAdapter

        can_config = self.config.interfaces['can']

        # Select adapter based on type
        if can_config['type'] == 'mock':
            self._can = MockCANAdapter(can_config)
        else:
            self._can = CANAdapter(can_config)
        
        result = self._can.initialize()
        if not result.success:
            raise RuntimeError(f"CAN initialization failed: {result.error}")
    
    def _initialize_serial(self):
        """Initialize serial interface"""
        from framework.adapters.serial_adapter import SerialAdapter
        from framework.adapters.mock_adapter import MockSerialAdapter

        serial_config = self.config.interfaces['serial']

        if serial_config['type'] == 'mock':
            self._serial = MockSerialAdapter(serial_config)
        else:
            self._serial = SerialAdapter(serial_config)
        
        result = self._serial.initialize()
        if not result.success:
            raise RuntimeError(f"Serial initialization failed: {result.error}")
    
    def _initialize_gpio(self):
        """Initialize GPIO interface"""
        from framework.adapters.gpio_adapter import GPIOAdapter
        from framework.adapters.mock_adapter import MockGPIOAdapter

        gpio_config = self.config.interfaces['gpio']

        if gpio_config['type'] == 'mock':
            self._gpio = MockGPIOAdapter(gpio_config)
        else:
            self._gpio = GPIOAdapter(gpio_config)
        
        result = self._gpio.initialize()
        if not result.success:
            raise RuntimeError(f"GPIO initialization failed: {result.error}")
    
    @property
    def can(self) -> "CANAdapter":
        """Get CAN interface adapter"""
        if self._can is None:
            raise RuntimeError("CAN interface not initialized or not configured")
        return self._can

    @property
    def serial(self) -> "SerialAdapter":
        """Get serial interface adapter"""
        if self._serial is None:
            raise RuntimeError("Serial interface not initialized or not configured")
        return self._serial

    @property
    def gpio(self) -> "GPIOAdapter":
        """Get GPIO interface adapter"""
        if self._gpio is None:
            raise RuntimeError("GPIO interface not initialized or not configured")
        return self._gpio

    def __getattr__(self, name):
        """
        Auto-discovery for dynamic adapters.

        Supports accessing adapters via {adapter_name}_interface pattern.
        Example: hardware.ethernet_interface automatically loads EthernetAdapter
        """
        if name.endswith('_interface'):
            adapter_name = name[:-10]  # Remove '_interface' suffix
            return self._get_or_create_adapter(adapter_name)

        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def _get_or_create_adapter(self, adapter_name: str):
        """
        Dynamically load and cache adapter by name.

        Args:
            adapter_name: Name of the adapter (e.g., 'ethernet', 'spi')

        Returns:
            Adapter instance

        Raises:
            RuntimeError: If adapter cannot be loaded or configured
        """
        # Check cache first
        if adapter_name in self._dynamic_adapters:
            return self._dynamic_adapters[adapter_name]

        try:
            # Try to import the adapter module
            module_name = f'framework.adapters.{adapter_name}_adapter'
            module = importlib.import_module(module_name)

            # Get the adapter class (e.g., EthernetAdapter)
            adapter_class_name = f'{adapter_name.title()}Adapter'
            adapter_class = getattr(module, adapter_class_name)

            # Get configuration for this adapter
            adapter_config = self.config.interfaces.get(adapter_name, {})

            # Check if we should use mock adapter
            if adapter_config.get('type') == 'mock':
                # Try to get mock version
                mock_class_name = f'Mock{adapter_class_name}'
                if hasattr(module, mock_class_name):
                    adapter_class = getattr(module, mock_class_name)
                    logger.debug(f"Using mock adapter for {adapter_name}")

            # Create adapter instance
            adapter_instance = adapter_class(adapter_config)

            # Cache the adapter
            self._dynamic_adapters[adapter_name] = adapter_instance

            logger.debug(f"Dynamically loaded adapter: {adapter_name}")
            return adapter_instance

        except ImportError as e:
            raise RuntimeError(
                f"Adapter '{adapter_name}' not found. "
                f"Make sure framework/adapters/{adapter_name}_adapter.py exists "
                f"with {adapter_name.title()}Adapter class. Error: {e}"
            )
        except AttributeError as e:
            raise RuntimeError(
                f"Adapter class '{adapter_class_name}' not found in module. "
                f"Make sure {adapter_name}_adapter.py contains class {adapter_class_name}. "
                f"Error: {e}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to create adapter '{adapter_name}': {e}"
            )

    def list_available_adapters(self) -> list[str]:
        """
        List all available adapters (both configured and discoverable).

        Returns:
            List of adapter names
        """
        import os
        from pathlib import Path

        available = []

        # Add configured interfaces
        available.extend(self.config.interfaces.keys())

        # Discover available adapter files
        adapters_dir = Path(__file__).parent.parent / "adapters"
        if adapters_dir.exists():
            for file in adapters_dir.glob("*_adapter.py"):
                if file.name != "base_adapter.py" and file.name != "__init__.py":
                    adapter_name = file.name.replace("_adapter.py", "")
                    if adapter_name not in available:
                        available.append(adapter_name)

        return sorted(available)

    def get_adapter_info(self, adapter_name: str) -> Dict[str, Any]:
        """
        Get information about a specific adapter.

        Args:
            adapter_name: Name of the adapter

        Returns:
            Dictionary with adapter information
        """
        info = {
            'name': adapter_name,
            'configured': adapter_name in self.config.interfaces,
            'loaded': adapter_name in self._dynamic_adapters,
            'available': False,
            'config': self.config.interfaces.get(adapter_name, {})
        }

        # Check if adapter file exists
        try:
            module_name = f'framework.adapters.{adapter_name}_adapter'
            importlib.import_module(module_name)
            info['available'] = True
        except ImportError:
            info['available'] = False

        return info
    
    def cleanup(self) -> OperationResult:
        """
        Clean up all hardware interfaces.
        Should be called at test teardown.

        Returns:
            OperationResult indicating success/failure
        """
        errors = []

        try:
            # Clean up legacy adapters
            if self._can:
                result = self._can.cleanup()
                if not result.success:
                    errors.append(f"CAN cleanup: {result.error}")

            if self._serial:
                result = self._serial.cleanup()
                if not result.success:
                    errors.append(f"Serial cleanup: {result.error}")

            if self._gpio:
                result = self._gpio.cleanup()
                if not result.success:
                    errors.append(f"GPIO cleanup: {result.error}")

            # Clean up dynamic adapters
            for adapter_name, adapter in self._dynamic_adapters.items():
                try:
                    if hasattr(adapter, 'cleanup'):
                        result = adapter.cleanup()
                        if not result.success:
                            errors.append(f"{adapter_name} cleanup: {result.error}")
                except Exception as e:
                    errors.append(f"{adapter_name} cleanup error: {e}")

            # Clear dynamic adapter cache
            self._dynamic_adapters.clear()

            self._initialized = False

            if errors:
                return OperationResult(
                    success=False,
                    error="; ".join(errors)
                )

            return OperationResult(success=True, log="HAL cleanup complete")

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"HAL cleanup failed: {str(e)}"
            )
    
    def is_initialized(self) -> bool:
        """Check if HAL is initialized"""
        return self._initialized
    
    def get_platform_info(self) -> Dict[str, str]:
        """
        Get information about current hardware platform.
        
        Returns:
            Dictionary with platform metadata
        """
        return {
            'name': self.config.platform.name,
            'version': self.config.platform.version,
            'vendor': self.config.platform.vendor,
            'description': self.config.platform.description,
        }
    
    def get_available_interfaces(self) -> list[str]:
        """
        Get list of available hardware interfaces.
        
        Returns:
            List of interface names
        """
        return list(self.config.interfaces.keys())
    
    def has_interface(self, interface_name: str) -> bool:
        """Check if interface is available"""
        return interface_name in self.config.interfaces
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()
    
    def __repr__(self):
        status = "initialized" if self._initialized else "not initialized"
        return f"HAL({self.config.platform.name}, {status})"
