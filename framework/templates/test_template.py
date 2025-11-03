"""
{{ADAPTER_NAME}} Test Template

This is a template for creating tests for new hardware adapters.
Replace all {{PLACEHOLDER}} values with your specific test implementation.

Usage:
1. Copy this file to tests/suites/{{adapter_name}}/test_{{adapter_name}}.py
2. Replace all {{PLACEHOLDER}} values
3. Add test metadata to config/test_registry.yaml
4. Implement your specific test logic
"""

from framework.core.test_decorators import auto_configure_test


class Test{{ADAPTER_CLASS}}:
    """Test class for {{ADAPTER_NAME}} adapter functionality"""

    @auto_configure_test
    def test_{{adapter_name}}_initialization(self, {{adapter_name}}_interface):
        """Test {{ADAPTER_NAME}} interface initialization"""
        result = {{adapter_name}}_interface.initialize()
        assert result.success, f"{{ADAPTER_NAME}} initialization failed: {result.error}"

        # Verify interface is ready
        assert {{adapter_name}}_interface.is_ready(), "Interface not ready after initialization"

        # Check status
        status = {{adapter_name}}_interface.get_status()
        assert status == "active", f"Expected 'active', got '{status}'"

    @auto_configure_test
    def test_{{adapter_name}}_cleanup(self, {{adapter_name}}_interface):
        """Test {{ADAPTER_NAME}} interface cleanup"""
        # Initialize first
        init_result = {{adapter_name}}_interface.initialize()
        assert init_result.success

        # Then cleanup
        cleanup_result = {{adapter_name}}_interface.cleanup()
        assert cleanup_result.success, f"{{ADAPTER_NAME}} cleanup failed: {cleanup_result.error}"

        # Verify interface is no longer ready
        assert not {{adapter_name}}_interface.is_ready(), "Interface still ready after cleanup"

    @auto_configure_test
    def test_{{adapter_name}}_send_data(self, {{adapter_name}}_interface):
        """Test sending data via {{ADAPTER_NAME}} interface"""
        # Initialize interface
        init_result = {{adapter_name}}_interface.initialize()
        assert init_result.success

        # TODO: Replace with your specific test data
        test_data = "test_{{adapter_name}}_data"

        # Send data
        result = {{adapter_name}}_interface.send_data(test_data)
        assert result.success, f"Failed to send data: {result.error}"

        # TODO: Add specific assertions for your adapter
        # Example: verify data format, response time, etc.

    @auto_configure_test
    def test_{{adapter_name}}_receive_data(self, {{adapter_name}}_interface):
        """Test receiving data from {{ADAPTER_NAME}} interface"""
        # Initialize interface
        init_result = {{adapter_name}}_interface.initialize()
        assert init_result.success

        # TODO: For real hardware, you might need to send data first
        # For mock adapters, this might return default/queued data

        # Receive data
        result = {{adapter_name}}_interface.receive_data(timeout=2.0)

        # TODO: Adapt this based on your adapter's behavior
        # Mock adapters might always return data
        # Real hardware might timeout if no data available
        if result.success:
            assert result.data is not None, "Received data should not be None"
            # TODO: Add specific data validation

    @auto_configure_test
    def test_{{adapter_name}}_configuration(self, {{adapter_name}}_interface):
        """Test {{ADAPTER_NAME}} configuration"""
        # Initialize interface
        init_result = {{adapter_name}}_interface.initialize()
        assert init_result.success

        # TODO: Replace with your adapter-specific configuration
        test_config = {
            'parameter1': 'value1',
            'parameter2': 123
        }

        # Configure adapter
        result = {{adapter_name}}_interface.configure(**test_config)
        assert result.success, f"Failed to configure {{ADAPTER_NAME}}: {result.error}"

    @auto_configure_test
    def test_{{adapter_name}}_error_handling(self, {{adapter_name}}_interface):
        """Test {{ADAPTER_NAME}} error handling"""
        # Test operations without initialization
        result = {{adapter_name}}_interface.send_data("test")
        assert not result.success, "Should fail when not initialized"
        assert "not initialized" in result.error.lower()

        result = {{adapter_name}}_interface.receive_data()
        assert not result.success, "Should fail when not initialized"
        assert "not initialized" in result.error.lower()

    # TODO: Add more specific tests for your adapter
    # Examples:

    @auto_configure_test
    def test_{{adapter_name}}_stress_test(self, {{adapter_name}}_interface):
        """Stress test {{ADAPTER_NAME}} with multiple operations"""
        # Initialize interface
        init_result = {{adapter_name}}_interface.initialize()
        assert init_result.success

        # TODO: Implement stress test specific to your adapter
        # Example: send multiple messages rapidly
        success_count = 0
        total_operations = 10

        for i in range(total_operations):
            result = {{adapter_name}}_interface.send_data(f"test_data_{i}")
            if result.success:
                success_count += 1

        # Allow some tolerance for real hardware
        assert success_count >= total_operations * 0.8, \
            f"Too many failures: {success_count}/{total_operations}"

    @auto_configure_test
    def test_{{adapter_name}}_data_integrity(self, {{adapter_name}}_interface):
        """Test data integrity through {{ADAPTER_NAME}} interface"""
        # Initialize interface
        init_result = {{adapter_name}}_interface.initialize()
        assert init_result.success

        # TODO: Implement data integrity test
        # Example: send known data, verify received data matches
        test_patterns = [
            "simple_string",
            "data_with_numbers_123",
            "special!@#$%^&*()characters"
        ]

        for pattern in test_patterns:
            # Send data
            send_result = {{adapter_name}}_interface.send_data(pattern)
            assert send_result.success

            # For mock adapters, this might echo back the data
            # For real hardware, you'd need to implement appropriate verification
            # TODO: Adapt based on your adapter's expected behavior


# TODO: If you have platform-specific tests, create separate test classes:

class Test{{ADAPTER_CLASS}}RealHardware:
    """Tests that require real {{ADAPTER_NAME}} hardware"""

    @auto_configure_test
    def test_{{adapter_name}}_hardware_specific_feature(self, {{adapter_name}}_interface):
        """Test feature that only works with real hardware"""
        # TODO: This test will be skipped on mock platform based on
        # test registry configuration
        pass


class Test{{ADAPTER_CLASS}}Mock:
    """Tests specific to mock {{ADAPTER_NAME}} adapter"""

    @auto_configure_test
    def test_{{adapter_name}}_mock_behavior(self, {{adapter_name}}_interface):
        """Test mock-specific behavior"""
        # TODO: Test mock adapter's specific behavior
        # Example: verify echo functionality, queue behavior, etc.
        pass