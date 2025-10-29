"""
CAN Bus Adapter

Provides interface to CAN bus communication using python-can library.
Supports SocketCAN, PCAN, Vector, and other interfaces.
"""

import can
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from framework.core.types import OperationResult
import logging

logger = logging.getLogger(__name__)


@dataclass
class CANMessage:
    """CAN message data structure"""
    arbitration_id: int
    data: List[int]
    is_extended_id: bool = False
    is_fd: bool = False
    timestamp: float = 0.0
    
    def to_can_message(self) -> can.Message:
        """Convert to python-can Message"""
        return can.Message(
            arbitration_id=self.arbitration_id,
            data=self.data,
            is_extended_id=self.is_extended_id,
            is_fd=self.is_fd
        )
    
    @classmethod
    def from_can_message(cls, msg: can.Message) -> 'CANMessage':
        """Create from python-can Message"""
        return cls(
            arbitration_id=msg.arbitration_id,
            data=list(msg.data),
            is_extended_id=msg.is_extended_id,
            is_fd=msg.is_fd,
            timestamp=msg.timestamp
        )


class CANAdapter:
    """
    CAN bus communication adapter.
    
    Usage:
        adapter = CANAdapter(config)
        adapter.initialize()
        
        # Send message
        result = adapter.send_message(0x123, [0x01, 0x02, 0x03])
        
        # Receive message
        msg = adapter.receive_message(timeout=1.0)
        
        # Add filter
        adapter.add_filter(0x100)
        
        adapter.cleanup()
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CAN adapter.
        
        Args:
            config: CAN interface configuration dictionary
        """
        self.config = config
        self.bus: Optional[can.BusABC] = None
        self.filters: List[int] = []
        self._initialized = False
    
    def initialize(self) -> OperationResult:
        """
        Initialize CAN interface.
        
        Returns:
            OperationResult with success/failure status
        """
        try:
            # Extract configuration
            interface = self.config.get('type', 'socketcan')
            channel = self.config['channel']
            bitrate = self.config['bitrate']
            fd = self.config.get('fd_enabled', False)
            
            logger.info(f"Initializing CAN bus: {interface} {channel} @ {bitrate}")
            
            # Create bus instance
            self.bus = can.Bus(
                interface=interface,
                channel=channel,
                bitrate=bitrate,
                fd=fd
            )
            
            self._initialized = True
            
            return OperationResult(
                success=True,
                log=f"CAN initialized: {channel} @ {bitrate} bps"
            )
        
        except Exception as e:
            logger.error(f"CAN initialization failed: {e}")
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    def send_message(self, arbitration_id: int, data: List[int], 
                     is_extended: bool = False) -> OperationResult:
        """
        Send CAN message.
        
        Args:
            arbitration_id: CAN message ID
            data: Message data bytes (0-8 bytes for CAN, 0-64 for CAN-FD)
            is_extended: Use extended ID format (29-bit)
        
        Returns:
            OperationResult with success/failure
        """
        if not self._initialized or self.bus is None:
            return OperationResult(
                success=False,
                error="CAN interface not initialized"
            )
        
        try:
            msg = can.Message(
                arbitration_id=arbitration_id,
                data=data,
                is_extended_id=is_extended
            )
            
            self.bus.send(msg)
            
            logger.debug(f"CAN TX: ID=0x{arbitration_id:X} Data={[hex(b) for b in data]}")
            
            return OperationResult(
                success=True,
                log=f"Sent CAN message ID 0x{arbitration_id:X}"
            )
        
        except Exception as e:
            logger.error(f"CAN send failed: {e}")
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    def receive_message(self, timeout: Optional[float] = None) -> Optional[CANMessage]:
        """
        Receive CAN message.
        
        Args:
            timeout: Timeout in seconds. None = blocking, 0 = non-blocking
        
        Returns:
            CANMessage if received, None if timeout or error
        """
        if not self._initialized or self.bus is None:
            logger.error("CAN interface not initialized")
            return None
        
        try:
            msg = self.bus.recv(timeout=timeout)
            
            if msg is None:
                return None
            
            logger.debug(
                f"CAN RX: ID=0x{msg.arbitration_id:X} "
                f"Data={[hex(b) for b in msg.data]}"
            )
            
            return CANMessage.from_can_message(msg)
        
        except Exception as e:
            logger.error(f"CAN receive failed: {e}")
            return None
    
    def add_filter(self, can_id: int, mask: int = 0x7FF) -> OperationResult:
        """
        Add CAN message filter.
        
        Args:
            can_id: CAN ID to filter
            mask: Filter mask (default 0x7FF for standard ID)
        
        Returns:
            OperationResult with success/failure
        """
        try:
            filter_config = [
                {"can_id": can_id, "can_mask": mask}
            ]
            
            if self.bus:
                self.bus.set_filters(filter_config)
            
            self.filters.append(can_id)
            
            logger.info(f"Added CAN filter: ID=0x{can_id:X} Mask=0x{mask:X}")
            
            return OperationResult(
                success=True,
                log=f"Filter added for ID 0x{can_id:X}"
            )
        
        except Exception as e:
            logger.error(f"Failed to add CAN filter: {e}")
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    def clear_filters(self) -> OperationResult:
        """
        Clear all CAN filters.
        
        Returns:
            OperationResult with success/failure
        """
        try:
            if self.bus:
                self.bus.set_filters(None)
            
            self.filters.clear()
            logger.info("CAN filters cleared")
            
            return OperationResult(success=True)
        
        except Exception as e:
            return OperationResult(success=False, error=str(e))
    
    def get_filters(self) -> List[int]:
        """Get list of active filters"""
        return self.filters.copy()
    
    def get_status(self) -> str:
        """Get bus status"""
        if not self._initialized:
            return "not_initialized"
        return "active" if self.bus else "error"
    
    def is_ready(self) -> bool:
        """Check if interface is ready"""
        return self._initialized and self.bus is not None
    
    def get_error_count(self) -> int:
        """Get error counter (if supported by interface)"""
        # This is hardware-specific and may not be supported by all interfaces
        try:
            if self.bus and hasattr(self.bus, 'get_stats'):
                stats = self.bus.get_stats()
                return stats.get('error_count', 0)
        except:
            pass
        return 0
    
    def flush_rx_buffer(self) -> int:
        """
        Flush receive buffer.
        
        Returns:
            Number of messages flushed
        """
        count = 0
        if self.bus:
            while self.receive_message(timeout=0) is not None:
                count += 1
        return count
    
    def cleanup(self) -> OperationResult:
        """
        Cleanup CAN interface.
        
        Returns:
            OperationResult with success/failure
        """
        try:
            if self.bus:
                self.bus.shutdown()
                self.bus = None
            
            self._initialized = False
            logger.info("CAN interface cleaned up")
            
            return OperationResult(success=True)
        
        except Exception as e:
            logger.error(f"CAN cleanup failed: {e}")
            return OperationResult(
                success=False,
                error=str(e)
            )
    
    def __repr__(self):
        status = "ready" if self.is_ready() else "not ready"
        channel = self.config.get('channel', 'unknown')
        return f"CANAdapter({channel}, {status})"
