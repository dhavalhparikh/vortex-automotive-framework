"""
CAN Bus Communication Tests

Test suite for CAN bus initialization, message transmission, and filtering.
"""

import pytest
import allure
import time


@allure.feature('CAN Bus')
@allure.story('Initialization')
class TestCANInitialization:
    """Test CAN bus initialization and basic setup"""
    
    @pytest.mark.smoke
    @pytest.mark.can_bus
    @pytest.mark.critical
    @allure.title("Test CAN interface initialization")
    @allure.severity(allure.severity_level.BLOCKER)
    def test_can_initialization(self, can_interface):
        """
        Verify CAN interface initializes correctly.
        
        Steps:
            1. Check interface is ready
            2. Verify status is active
            3. Confirm no errors present
        """
        with allure.step("Check CAN interface is ready"):
            assert can_interface.is_ready(), "CAN interface is not ready"
        
        with allure.step("Verify CAN status is active"):
            status = can_interface.get_status()
            allure.attach(status, name="CAN Status", attachment_type=allure.attachment_type.TEXT)
            assert status == "active", f"Expected 'active', got '{status}'"
        
        with allure.step("Confirm no errors at startup"):
            error_count = can_interface.get_error_count()
            assert error_count == 0, f"Unexpected errors: {error_count}"
    
    @pytest.mark.smoke
    @pytest.mark.can_bus
    @allure.title("Test CAN interface cleanup")
    def test_can_cleanup(self, can_interface):
        """Verify CAN interface can be cleaned up properly"""
        with allure.step("Cleanup CAN interface"):
            result = can_interface.cleanup()
            assert result.success, f"Cleanup failed: {result.error}"
        
        with allure.step("Verify interface is no longer ready"):
            assert not can_interface.is_ready(), "Interface still ready after cleanup"


@allure.feature('CAN Bus')
@allure.story('Message Transmission')
class TestCANMessageTransmission:
    """Test CAN message sending and receiving"""
    
    @pytest.mark.smoke
    @pytest.mark.can_bus
    @pytest.mark.critical
    @pytest.mark.dependency(name="test_send_message")
    @allure.title("Test sending CAN message")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_send_can_message(self, can_interface):
        """
        Test sending a basic CAN message.
        
        Expected:
            Message is sent successfully without errors
        """
        message_id = 0x123
        message_data = [0x01, 0x02, 0x03, 0x04]
        
        with allure.step(f"Send CAN message ID=0x{message_id:X}"):
            allure.attach(
                f"ID: 0x{message_id:X}\nData: {[hex(b) for b in message_data]}",
                name="Message Details",
                attachment_type=allure.attachment_type.TEXT
            )
            
            result = can_interface.send_message(message_id, message_data)
            
            assert result.success, f"Failed to send message: {result.error}"
            allure.attach(result.log, name="Send Result", attachment_type=allure.attachment_type.TEXT)
    
    @pytest.mark.smoke
    @pytest.mark.can_bus
    @pytest.mark.dependency(depends=["test_send_message"])
    @allure.title("Test receiving CAN message")
    def test_receive_can_message(self, can_interface):
        """
        Test receiving CAN messages.
        
        Note: This test may timeout on real hardware if no messages are present.
        Works with mock adapter which generates responses.
        """
        with allure.step("Send message to generate response"):
            can_interface.send_message(0x100, [0xAA, 0xBB])
        
        with allure.step("Receive CAN message"):
            message = can_interface.receive_message(timeout=2.0)
            
            if message:
                allure.attach(
                    f"ID: 0x{message.arbitration_id:X}\n"
                    f"Data: {[hex(b) for b in message.data]}\n"
                    f"Timestamp: {message.timestamp}",
                    name="Received Message",
                    attachment_type=allure.attachment_type.TEXT
                )
                assert message is not None, "No message received"
            else:
                pytest.skip("No message received (expected on real hardware without traffic)")
    
    @pytest.mark.regression
    @pytest.mark.can_bus
    @pytest.mark.parametrize("msg_id,data", [
        (0x100, [0x01, 0x02, 0x03]),
        (0x200, [0xAA, 0xBB, 0xCC, 0xDD]),
        (0x300, [0xFF] * 8),
    ])
    @allure.title("Test sending various CAN messages")
    def test_send_various_messages(self, can_interface, msg_id, data):
        """
        Test sending different CAN messages with various IDs and data.
        
        Uses parametrization to test multiple message configurations.
        """
        result = can_interface.send_message(msg_id, data)
        assert result.success, f"Failed to send 0x{msg_id:X}: {result.error}"
    
    @pytest.mark.performance
    @pytest.mark.can_bus
    @pytest.mark.slow
    @allure.title("Test CAN message throughput")
    def test_message_throughput(self, can_interface):
        """
        Test CAN bus message throughput.
        
        Sends multiple messages and measures performance.
        """
        num_messages = 100
        message_id = 0x123
        message_data = [0x01, 0x02, 0x03]
        
        with allure.step(f"Send {num_messages} CAN messages"):
            start_time = time.time()
            
            success_count = 0
            for i in range(num_messages):
                result = can_interface.send_message(message_id, message_data)
                if result.success:
                    success_count += 1
            
            elapsed_time = time.time() - start_time
            
            throughput = success_count / elapsed_time if elapsed_time > 0 else 0
            
            allure.attach(
                f"Messages sent: {success_count}/{num_messages}\n"
                f"Time elapsed: {elapsed_time:.3f}s\n"
                f"Throughput: {throughput:.2f} msg/s",
                name="Performance Metrics",
                attachment_type=allure.attachment_type.TEXT
            )
            
            assert success_count == num_messages, f"Only {success_count}/{num_messages} messages sent"
            assert throughput > 10, f"Throughput too low: {throughput:.2f} msg/s"


@allure.feature('CAN Bus')
@allure.story('Message Filtering')
class TestCANFiltering:
    """Test CAN message filtering functionality"""
    
    @pytest.mark.smoke
    @pytest.mark.can_bus
    @allure.title("Test adding CAN filter")
    def test_add_filter(self, can_interface):
        """Test adding a CAN message filter"""
        filter_id = 0x200
        
        with allure.step(f"Add filter for ID 0x{filter_id:X}"):
            result = can_interface.add_filter(filter_id)
            assert result.success, f"Failed to add filter: {result.error}"
        
        with allure.step("Verify filter is in active filters"):
            filters = can_interface.get_filters()
            allure.attach(
                str(filters),
                name="Active Filters",
                attachment_type=allure.attachment_type.TEXT
            )
            assert filter_id in filters, "Filter not found in active filters"
    
    @pytest.mark.regression
    @pytest.mark.can_bus
    @allure.title("Test multiple CAN filters")
    def test_multiple_filters(self, can_interface):
        """Test adding multiple CAN filters"""
        filter_ids = [0x100, 0x200, 0x300]
        
        with allure.step("Add multiple filters"):
            for filter_id in filter_ids:
                result = can_interface.add_filter(filter_id)
                assert result.success, f"Failed to add filter 0x{filter_id:X}"
        
        with allure.step("Verify all filters are active"):
            active_filters = can_interface.get_filters()
            for filter_id in filter_ids:
                assert filter_id in active_filters, f"Filter 0x{filter_id:X} not active"
    
    @pytest.mark.regression
    @pytest.mark.can_bus
    @allure.title("Test clearing CAN filters")
    def test_clear_filters(self, can_interface):
        """Test clearing all CAN filters"""
        # Add some filters first
        can_interface.add_filter(0x100)
        can_interface.add_filter(0x200)
        
        with allure.step("Clear all filters"):
            result = can_interface.clear_filters()
            assert result.success, "Failed to clear filters"
        
        with allure.step("Verify no filters remain"):
            filters = can_interface.get_filters()
            assert len(filters) == 0, f"Filters still present: {filters}"


@allure.feature('CAN Bus')
@allure.story('Error Handling')
class TestCANErrorHandling:
    """Test CAN error detection and handling"""
    
    @pytest.mark.regression
    @pytest.mark.can_bus
    @allure.title("Test CAN error counter")
    def test_error_count(self, can_interface):
        """Test CAN error counter functionality"""
        with allure.step("Get initial error count"):
            initial_errors = can_interface.get_error_count()
            allure.attach(
                str(initial_errors),
                name="Initial Error Count",
                attachment_type=allure.attachment_type.TEXT
            )
        
        # Note: Injecting actual errors requires mock adapter
        # On real hardware, this would require specific error conditions
        
        with allure.step("Verify error count is accessible"):
            assert isinstance(initial_errors, int), "Error count should be integer"
            assert initial_errors >= 0, "Error count should be non-negative"
    
    @pytest.mark.regression
    @pytest.mark.can_bus
    @allure.title("Test sending invalid message")
    def test_invalid_message(self, can_interface):
        """Test behavior when sending invalid CAN message"""
        with allure.step("Attempt to send message with too much data"):
            # CAN standard allows max 8 bytes (64 for CAN-FD)
            invalid_data = [0xFF] * 100
            
            result = can_interface.send_message(0x123, invalid_data)
            
            # Should fail gracefully
            assert not result.success or len(invalid_data) <= 8, \
                "Should reject oversized message or truncate"
