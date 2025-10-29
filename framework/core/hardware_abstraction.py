"""
Hardware Abstraction Layer (HAL)

Provides a unified interface to access different hardware components
regardless of the underlying platform.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass

from framework.core.config_loader import ConfigLoader, HardwareConfig
from framework.adapters.can_adapter import CANAdapter
from framework.adapters.serial_adapter import SerialAdapter
from framework.adapters.gpio_adapter import GPIOAdapter
from framework.adapters.mock_adapter import MockCANAdapter, MockSerialAdapter, MockGPIOAdapter


@dataclass
class OperationResult:
    """Result of a hardware operation"""
    success: bool
    error: Optional[str] = None
    data: Optional[Any] = None
    log: str = ""
    
    def __bool__(self):
        return self.success


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
        
        # Interface adapters
        self._can: Optional[CANAdapter] = None
        self._serial: Optional[SerialAdapter] = None
        self._gpio: Optional[GPIOAdapter] = None
        
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
        gpio_config = self.config.interfaces['gpio']
        
        if gpio_config['type'] == 'mock':
            self._gpio = MockGPIOAdapter(gpio_config)
        else:
            self._gpio = GPIOAdapter(gpio_config)
        
        result = self._gpio.initialize()
        if not result.success:
            raise RuntimeError(f"GPIO initialization failed: {result.error}")
    
    @property
    def can(self) -> CANAdapter:
        """Get CAN interface adapter"""
        if self._can is None:
            raise RuntimeError("CAN interface not initialized or not configured")
        return self._can
    
    @property
    def serial(self) -> SerialAdapter:
        """Get serial interface adapter"""
        if self._serial is None:
            raise RuntimeError("Serial interface not initialized or not configured")
        return self._serial
    
    @property
    def gpio(self) -> GPIOAdapter:
        """Get GPIO interface adapter"""
        if self._gpio is None:
            raise RuntimeError("GPIO interface not initialized or not configured")
        return self._gpio
    
    def cleanup(self) -> OperationResult:
        """
        Clean up all hardware interfaces.
        Should be called at test teardown.
        
        Returns:
            OperationResult indicating success/failure
        """
        errors = []
        
        try:
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
