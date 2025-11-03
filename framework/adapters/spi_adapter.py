"""
SPI Adapter

SPI (Serial Peripheral Interface) adapter for communication with SPI devices.
"""

from framework.core.types import OperationResult


class SpiAdapter:
    """
    SPI interface adapter

    Handles communication with SPI devices.
    """

    def __init__(self, config):
        self.config = config
        self.device_path = config.get('device_path', '/dev/spidev0.0')
        self.speed = config.get('speed', 1000000)  # 1 MHz default
        self.mode = config.get('mode', 0)  # SPI mode 0

        # Initialize internal state
        self._is_initialized = False
        self._device_handle = None

    def initialize(self) -> OperationResult:
        """
        Initialize the SPI interface

        Returns:
            OperationResult: Success/failure with details
        """
        try:
            # For real hardware, you'd open the SPI device here
            # import spidev
            # self._device_handle = spidev.SpiDev()
            # self._device_handle.open(0, 0)  # Bus 0, Device 0
            # self._device_handle.max_speed_hz = self.speed
            # self._device_handle.mode = self.mode

            # For template - simulate successful initialization
            self._device_handle = "mock_spi_handle"
            self._is_initialized = True
            return OperationResult(
                success=True,
                log=f"SPI initialized on {self.device_path} at {self.speed} Hz"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to initialize SPI: {str(e)}"
            )

    def cleanup(self) -> OperationResult:
        """
        Clean up the SPI interface

        Returns:
            OperationResult: Success/failure with details
        """
        try:
            if self._device_handle and self._device_handle != "mock_spi_handle":
                # self._device_handle.close()
                pass

            self._device_handle = None
            self._is_initialized = False
            return OperationResult(
                success=True,
                log="SPI cleaned up successfully"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to cleanup SPI: {str(e)}"
            )

    def is_ready(self) -> bool:
        """
        Check if the adapter is ready for operations

        Returns:
            bool: True if ready, False otherwise
        """
        # TODO: Implement your readiness check
        return self._is_initialized and self._device_handle is not None

    def get_status(self) -> str:
        """
        Get current adapter status

        Returns:
            str: Status description
        """
        if self.is_ready():
            return "active"
        else:
            return "inactive"

    # TODO: Add your custom methods below
    # Example methods:

    def transfer(self, data: list) -> OperationResult:
        """
        Transfer data via SPI interface (full duplex)

        Args:
            data: List of bytes to send

        Returns:
            OperationResult: Success/failure with response data
        """
        if not self.is_ready():
            return OperationResult(
                success=False,
                error="SPI not initialized"
            )

        try:
            # For real hardware:
            # response = self._device_handle.xfer2(data)

            # For template - echo back with modification
            response = [b + 1 for b in data]  # Increment each byte

            return OperationResult(
                success=True,
                data=response,
                log=f"SPI transfer: sent {len(data)} bytes, received {len(response)} bytes"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to transfer data: {str(e)}"
            )

    def receive_data(self, timeout: float = 1.0) -> OperationResult:
        """
        Receive data from {{ADAPTER_NAME}} interface

        Args:
            timeout: Timeout in seconds

        Returns:
            OperationResult: Success/failure with received data
        """
        if not self.is_ready():
            return OperationResult(
                success=False,
                error="{{ADAPTER_NAME}} not initialized"
            )

        try:
            # TODO: Implement your receive logic
            # data = receive_from_device(self._device_handle, timeout)

            # For template - return dummy data
            data = "dummy_response_data"

            return OperationResult(
                success=True,
                data=data,
                log=f"Received data from {{ADAPTER_NAME}}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to receive data: {str(e)}"
            )

    def configure(self, **kwargs) -> OperationResult:
        """
        Configure {{ADAPTER_NAME}} parameters

        Args:
            **kwargs: Configuration parameters specific to your adapter

        Returns:
            OperationResult: Success/failure with details
        """
        try:
            # TODO: Implement your configuration logic
            # Example:
            # if 'baudrate' in kwargs:
            #     set_baudrate(self._device_handle, kwargs['baudrate'])
            # if 'mode' in kwargs:
            #     set_mode(self._device_handle, kwargs['mode'])

            return OperationResult(
                success=True,
                log=f"{{ADAPTER_NAME}} configured with {kwargs}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to configure {{ADAPTER_NAME}}: {str(e)}"
            )


class MockSpiAdapter(SpiAdapter):
    """
    Mock SPI adapter for testing without hardware
    """

    def __init__(self, config):
        super().__init__(config)
        self._mock_data_queue = []

    def initialize(self) -> OperationResult:
        """Mock initialization - always succeeds"""
        self._is_initialized = True
        self._device_handle = "mock_spi_handle"
        return OperationResult(
            success=True,
            log=f"Mock SPI initialized on {self.device_path}"
        )

    def transfer(self, data: list) -> OperationResult:
        """Mock SPI transfer - returns modified data"""
        if not self.is_ready():
            return OperationResult(success=False, error="Not initialized")

        # Mock behavior: invert the bytes
        response = [0xFF - b for b in data]

        return OperationResult(
            success=True,
            data=response,
            log=f"Mock SPI transfer: {len(data)} bytes processed"
        )