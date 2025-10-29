"""
Mock Adapters

Simulated hardware adapters for testing without actual hardware.
Perfect for CI/CD pipelines and development.
"""

from typing import List, Optional, Dict, Any
from framework.core.types import OperationResult
from framework.adapters.can_adapter import CANMessage
import logging
import time
import random

logger = logging.getLogger(__name__)


class MockCANAdapter:
    """
    Mock CAN adapter that simulates CAN bus behavior.
    
    Provides same interface as real CAN adapter but with simulated responses.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.filters: List[int] = []
        self._initialized = False
        self._message_queue: List[CANMessage] = []
        self._error_count = 0
        self._send_count = 0
        self._recv_count = 0
    
    def initialize(self) -> OperationResult:
        """Initialize mock CAN interface"""
        logger.info(f"Mock CAN initialized: {self.config.get('channel', 'vcan0')}")
        self._initialized = True
        return OperationResult(
            success=True,
            log="Mock CAN interface initialized"
        )
    
    def send_message(self, arbitration_id: int, data: List[int],
                     is_extended: bool = False) -> OperationResult:
        """Simulate sending CAN message"""
        if not self._initialized:
            return OperationResult(
                success=False,
                error="Mock CAN not initialized"
            )
        
        self._send_count += 1
        logger.debug(
            f"Mock CAN TX: ID=0x{arbitration_id:X} Data={[hex(b) for b in data]}"
        )
        
        # Simulate response message (echo with modified data)
        response = CANMessage(
            arbitration_id=arbitration_id + 0x08,  # Response ID
            data=[d + 1 for d in data],  # Increment data
            is_extended_id=is_extended,
            timestamp=time.time()
        )
        self._message_queue.append(response)
        
        return OperationResult(success=True, log=f"Mock sent ID 0x{arbitration_id:X}")
    
    def receive_message(self, timeout: Optional[float] = None) -> Optional[CANMessage]:
        """Simulate receiving CAN message"""
        if not self._initialized:
            return None
        
        # Return queued messages first
        if self._message_queue:
            msg = self._message_queue.pop(0)
            self._recv_count += 1
            logger.debug(f"Mock CAN RX: ID=0x{msg.arbitration_id:X}")
            return msg
        
        # Simulate no message available
        if timeout == 0:
            return None
        
        # For blocking calls, simulate periodic messages
        if timeout and timeout > 0:
            time.sleep(min(timeout, 0.1))
            
            # Generate random message
            msg = CANMessage(
                arbitration_id=random.choice([0x100, 0x200, 0x300]),
                data=[random.randint(0, 255) for _ in range(8)],
                timestamp=time.time()
            )
            self._recv_count += 1
            return msg
        
        return None
    
    def add_filter(self, can_id: int, mask: int = 0x7FF) -> OperationResult:
        """Add mock filter"""
        self.filters.append(can_id)
        logger.info(f"Mock CAN filter added: 0x{can_id:X}")
        return OperationResult(success=True)
    
    def clear_filters(self) -> OperationResult:
        """Clear mock filters"""
        self.filters.clear()
        return OperationResult(success=True)
    
    def get_filters(self) -> List[int]:
        """Get active filters"""
        return self.filters.copy()
    
    def get_status(self) -> str:
        """Get mock status"""
        return "active" if self._initialized else "not_initialized"
    
    def is_ready(self) -> bool:
        """Check if ready"""
        return self._initialized
    
    def get_error_count(self) -> int:
        """Get simulated error count"""
        return self._error_count
    
    def inject_error(self) -> None:
        """Inject simulated error for testing"""
        self._error_count += 1
    
    def flush_rx_buffer(self) -> int:
        """Flush message queue"""
        count = len(self._message_queue)
        self._message_queue.clear()
        return count
    
    def cleanup(self) -> OperationResult:
        """Cleanup mock interface"""
        self._initialized = False
        self._message_queue.clear()
        logger.info("Mock CAN cleaned up")
        return OperationResult(success=True)
    
    def __repr__(self):
        return f"MockCANAdapter({self.config.get('channel', 'vcan0')})"


class MockSerialAdapter:
    """Mock serial/UART adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self._read_buffer = b""
    
    def initialize(self) -> OperationResult:
        """Initialize mock serial"""
        logger.info(f"Mock Serial initialized: {self.config.get('port', 'mock')}")
        self._initialized = True
        return OperationResult(success=True, log="Mock serial initialized")
    
    def write(self, data: bytes) -> OperationResult:
        """Simulate writing data"""
        if not self._initialized:
            return OperationResult(success=False, error="Not initialized")
        
        logger.debug(f"Mock Serial TX: {data.hex()}")
        
        # Echo data back to read buffer
        self._read_buffer += data
        
        return OperationResult(success=True, data=len(data))
    
    def read(self, size: int = 1) -> Optional[bytes]:
        """Simulate reading data"""
        if not self._initialized:
            return None
        
        if len(self._read_buffer) >= size:
            data = self._read_buffer[:size]
            self._read_buffer = self._read_buffer[size:]
            logger.debug(f"Mock Serial RX: {data.hex()}")
            return data
        
        return b""
    
    def read_line(self, timeout: Optional[float] = None) -> Optional[str]:
        """Simulate reading line"""
        if not self._initialized:
            return None
        
        # Return mock response
        return "OK\r\n"
    
    def is_open(self) -> bool:
        """Check if open"""
        return self._initialized
    
    def flush(self) -> None:
        """Flush buffers"""
        self._read_buffer = b""
    
    def cleanup(self) -> OperationResult:
        """Cleanup mock serial"""
        self._initialized = False
        self._read_buffer = b""
        logger.info("Mock Serial cleaned up")
        return OperationResult(success=True)
    
    def __repr__(self):
        return f"MockSerialAdapter({self.config.get('port', 'mock')})"


class MockGPIOAdapter:
    """Mock GPIO adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._initialized = False
        self._pin_states: Dict[int, bool] = {}
    
    def initialize(self) -> OperationResult:
        """Initialize mock GPIO"""
        logger.info("Mock GPIO initialized")
        self._initialized = True
        
        # Initialize all pins to False
        for pin_name, pin_num in self.config.get('pins', {}).items():
            self._pin_states[pin_num] = False
        
        return OperationResult(success=True, log="Mock GPIO initialized")
    
    def set_pin(self, pin: int, value: bool) -> OperationResult:
        """Set mock pin state"""
        if not self._initialized:
            return OperationResult(success=False, error="Not initialized")
        
        self._pin_states[pin] = value
        logger.debug(f"Mock GPIO: Pin {pin} = {value}")
        
        return OperationResult(success=True)
    
    def get_pin(self, pin: int) -> Optional[bool]:
        """Get mock pin state"""
        if not self._initialized:
            return None
        
        return self._pin_states.get(pin, False)
    
    def toggle_pin(self, pin: int) -> OperationResult:
        """Toggle mock pin"""
        current = self.get_pin(pin)
        return self.set_pin(pin, not current)
    
    def cleanup(self) -> OperationResult:
        """Cleanup mock GPIO"""
        self._initialized = False
        self._pin_states.clear()
        logger.info("Mock GPIO cleaned up")
        return OperationResult(success=True)
    
    def __repr__(self):
        return "MockGPIOAdapter()"
