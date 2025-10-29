"""
Serial/UART Adapter

Provides interface to serial communication using pyserial.
"""

import serial
from typing import Optional, Dict, Any
from framework.core.types import OperationResult
import logging

logger = logging.getLogger(__name__)


class SerialAdapter:
    """Serial/UART communication adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.port: Optional[serial.Serial] = None
        self._initialized = False
    
    def initialize(self) -> OperationResult:
        """Initialize serial port"""
        try:
            self.port = serial.Serial(
                port=self.config['port'],
                baudrate=self.config.get('baudrate', 115200),
                bytesize=self.config.get('bytesize', 8),
                parity=self.config.get('parity', 'N'),
                stopbits=self.config.get('stopbits', 1),
                timeout=self.config.get('timeout', 1.0)
            )
            self._initialized = True
            logger.info(f"Serial initialized: {self.config['port']}")
            return OperationResult(success=True)
        except Exception as e:
            logger.error(f"Serial init failed: {e}")
            return OperationResult(success=False, error=str(e))
    
    def write(self, data: bytes) -> OperationResult:
        """Write data to serial port"""
        if not self._initialized or not self.port:
            return OperationResult(success=False, error="Not initialized")
        try:
            bytes_written = self.port.write(data)
            return OperationResult(success=True, data=bytes_written)
        except Exception as e:
            return OperationResult(success=False, error=str(e))
    
    def read(self, size: int = 1) -> Optional[bytes]:
        """Read data from serial port"""
        if not self._initialized or not self.port:
            return None
        try:
            return self.port.read(size)
        except Exception as e:
            logger.error(f"Serial read failed: {e}")
            return None
    
    def read_line(self, timeout: Optional[float] = None) -> Optional[str]:
        """Read line from serial port"""
        if not self._initialized or not self.port:
            return None
        try:
            if timeout:
                self.port.timeout = timeout
            line = self.port.readline()
            return line.decode('utf-8', errors='ignore').strip()
        except Exception as e:
            logger.error(f"Serial readline failed: {e}")
            return None
    
    def is_open(self) -> bool:
        """Check if port is open"""
        return self._initialized and self.port is not None and self.port.is_open
    
    def flush(self) -> None:
        """Flush buffers"""
        if self.port:
            self.port.flush()
    
    def cleanup(self) -> OperationResult:
        """Cleanup serial port"""
        try:
            if self.port and self.port.is_open:
                self.port.close()
            self._initialized = False
            logger.info("Serial cleaned up")
            return OperationResult(success=True)
        except Exception as e:
            return OperationResult(success=False, error=str(e))
