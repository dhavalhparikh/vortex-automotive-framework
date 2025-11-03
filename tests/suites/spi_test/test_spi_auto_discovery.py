"""
SPI Auto-Discovery Test

This test validates that the new simplified adapter creation process works:
1. SPI adapter auto-discovery via hardware.spi_interface
2. Auto-generated fixture via spi_interface parameter
3. Mock adapter automatic selection
"""

from framework.core.test_decorators import auto_configure_test


@auto_configure_test
def test_spi_auto_discovery(spi_interface):
    """Test that SPI adapter is auto-discovered and works"""
    # Test initialization
    result = spi_interface.initialize()
    assert result.success, f"SPI initialization failed: {result.error}"

    # Verify interface is ready
    assert spi_interface.is_ready(), "SPI interface not ready after initialization"

    # Test SPI transfer
    test_data = [0x01, 0x02, 0x03, 0x04]
    result = spi_interface.transfer(test_data)
    assert result.success, f"SPI transfer failed: {result.error}"
    assert result.data is not None, "No response data from SPI transfer"

    # Verify mock behavior (inverts bytes: 0x01 -> 0xFE, etc.)
    expected = [0xFE, 0xFD, 0xFC, 0xFB]  # 0xFF - original values
    assert result.data == expected, f"Expected {expected}, got {result.data}"

    print(f"✅ SPI auto-discovery test passed! Sent: {test_data}, Received: {result.data}")


@auto_configure_test
def test_spi_adapter_type_detection():
    """Test that mock adapter is automatically selected"""
    import os
    from framework.core.hardware_abstraction import HardwareAbstractionLayer

    # Create HAL instance
    hal = HardwareAbstractionLayer()

    # Access SPI interface via auto-discovery
    spi = hal.spi_interface

    # Verify it's the mock adapter
    assert spi.__class__.__name__ == "MockSpiAdapter", f"Expected MockSpiAdapter, got {spi.__class__.__name__}"

    print(f"✅ Mock adapter auto-detection works! Class: {spi.__class__.__name__}")


@auto_configure_test
def test_spi_configuration_loading():
    """Test that SPI configuration is loaded correctly"""
    import os
    from framework.core.hardware_abstraction import HardwareAbstractionLayer

    hal = HardwareAbstractionLayer()
    spi = hal.spi_interface

    # Check configuration values
    assert spi.device_path == "/dev/spidev0.0", f"Wrong device path: {spi.device_path}"
    assert spi.speed == 1000000, f"Wrong speed: {spi.speed}"
    assert spi.mode == 0, f"Wrong mode: {spi.mode}"

    print(f"✅ SPI configuration loaded correctly: {spi.device_path} @ {spi.speed} Hz")


@auto_configure_test
def test_adapter_info_and_discovery():
    """Test HAL's adapter discovery features"""
    from framework.core.hardware_abstraction import HardwareAbstractionLayer

    hal = HardwareAbstractionLayer()

    # Test list available adapters
    available = hal.list_available_adapters()
    assert "spi" in available, f"SPI not in available adapters: {available}"

    # Test adapter info
    info = hal.get_adapter_info("spi")
    assert info["name"] == "spi"
    assert info["configured"] == True  # Configured in mock_platform.yaml
    assert info["available"] == True   # spi_adapter.py exists

    print(f"✅ Adapter discovery working! Available adapters: {available}")
    print(f"   SPI info: {info}")