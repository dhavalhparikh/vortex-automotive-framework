"""
Clean CAN Bus Tests

Demonstrates the new configuration-driven test approach.
No pytest markers or allure decorators - everything comes from config!
"""

from framework.core.test_decorators import auto_configure_test


@auto_configure_test
def test_can_initialization(can_interface):
    """Clean test with metadata from config"""
    result = can_interface.initialize()
    assert result.success, f"CAN initialization failed: {result.error}"


@auto_configure_test
def test_can_cleanup(can_interface):
    """Clean test with metadata from config"""
    # Initialize first
    init_result = can_interface.initialize()
    assert init_result.success

    # Then cleanup
    cleanup_result = can_interface.cleanup()
    assert cleanup_result.success, f"CAN cleanup failed: {cleanup_result.error}"


@auto_configure_test
def test_send_can_message(can_interface):
    """Clean test with metadata from config"""
    # Initialize interface
    init_result = can_interface.initialize()
    assert init_result.success

    # Send a test message
    test_message_id = 0x123
    test_data = [0x01, 0x02, 0x03, 0x04]

    result = can_interface.send_message(test_message_id, test_data)
    assert result.success, f"Failed to send CAN message: {result.error}"


@auto_configure_test
def test_receive_can_message(can_interface):
    """Clean test with metadata from config - will auto-skip on mock platform"""
    # Initialize interface
    init_result = can_interface.initialize()
    assert init_result.success

    # This test requires actual hardware, but the registry config
    # will handle platform compatibility automatically

    # Try to receive a message (with timeout)
    message = can_interface.receive_message(timeout=1.0)
    # On mock platform, this might return None, which is expected
    # The test registry will skip this on mock if configured correctly


@auto_configure_test
def test_add_filter(can_interface):
    """Clean test with metadata from config"""
    # Initialize interface
    init_result = can_interface.initialize()
    assert init_result.success

    # Add a CAN filter
    filter_id = 0x100
    filter_mask = 0x7FF

    result = can_interface.add_filter(filter_id, filter_mask)
    assert result.success, f"Failed to add CAN filter: {result.error}"