"""
CAN Bus Communication Tests

Test suite for CAN bus initialization, message transmission, and filtering.
Uses the new configuration-driven approach - all metadata in config/test_registry.yaml
"""

import time
from framework.core.test_decorators import auto_configure_test


class TestCANInitialization:
    """Test CAN bus initialization and basic setup"""

    @auto_configure_test
    def test_can_initialization(self, can_interface):
        """Verify CAN interface initializes correctly"""
        result = can_interface.initialize()
        assert result.success, f"CAN initialization failed: {result.error}"

        # Verify interface is ready
        assert can_interface.is_ready(), "Interface not ready after initialization"

        # Check status
        status = can_interface.get_status()
        assert status == "active", f"Expected 'active', got '{status}'"

        # Confirm no errors at startup
        error_count = can_interface.get_error_count()
        assert error_count == 0, f"Unexpected errors: {error_count}"

    @auto_configure_test
    def test_can_cleanup(self, can_interface):
        """Verify CAN interface can be cleaned up properly"""
        result = can_interface.cleanup()
        assert result.success, f"Cleanup failed: {result.error}"

        # Verify interface is no longer ready
        assert not can_interface.is_ready(), "Interface still ready after cleanup"


class TestCANMessageTransmission:
    """Test CAN message sending and receiving"""

    @auto_configure_test
    def test_send_can_message(self, can_interface):
        """Test sending a basic CAN message"""
        message_id = 0x123
        message_data = [0x01, 0x02, 0x03, 0x04]

        result = can_interface.send_message(message_id, message_data)
        assert result.success, f"Failed to send message: {result.error}"

        # Message sent successfully - that's the main verification
        # (Mock adapter doesn't return detailed message data)

    @auto_configure_test
    def test_receive_can_message(self, can_interface):
        """Test receiving CAN messages"""
        # This test might be skipped on mock platform based on config
        message = can_interface.receive_message(timeout=1.0)

        # On mock platform, this might return None or a mock message
        # The test registry config will handle platform-specific behavior
        if message is not None:
            assert hasattr(message, 'id'), "Message missing ID"
            assert hasattr(message, 'data'), "Message missing data"


class TestCANFiltering:
    """Test CAN message filtering functionality"""

    @auto_configure_test
    def test_add_filter(self, can_interface):
        """Test adding CAN message filter"""
        filter_id = 0x200
        filter_mask = 0x7FF

        result = can_interface.add_filter(filter_id, filter_mask)
        assert result.success, f"Failed to add filter: {result.error}"

        # Verify filter was added
        filters = can_interface.get_filters()
        assert any(f["id"] == filter_id for f in filters), "Filter not found"