"""
{{ADAPTER_NAME}} Adapter Template

This is a template for creating new hardware adapters.
Replace all {{PLACEHOLDER}} values with your specific implementation.

Usage:
1. Copy this file to framework/adapters/{{adapter_name}}_adapter.py
2. Replace all {{PLACEHOLDER}} values
3. Implement the TODO methods
4. Add device config to config/hardware/your_platform.yaml
"""

from framework.core.types import OperationResult


class {{ADAPTER_CLASS}}:
    """
    {{ADAPTER_NAME}} interface adapter

    Handles communication with {{ADAPTER_NAME}} devices.
    Replace this docstring with your adapter's specific functionality.
    """

    def __init__(self, config):
        self.config = config
        self.device_path = config.get('device_path', '{{DEVICE_PATH}}')
        # TODO: Add your adapter-specific configuration parameters
        # self.baudrate = config.get('baudrate', 115200)
        # self.timeout = config.get('timeout', 5.0)

        # TODO: Initialize any internal state
        self._is_initialized = False
        self._device_handle = None

    def initialize(self) -> OperationResult:
        """
        Initialize the {{ADAPTER_NAME}} interface

        Returns:
            OperationResult: Success/failure with details
        """
        try:
            # TODO: Implement your initialization logic
            # Example:
            # self._device_handle = open_device(self.device_path)
            # configure_device(self._device_handle, self.baudrate)

            self._is_initialized = True
            return OperationResult(
                success=True,
                log=f"{{ADAPTER_NAME}} initialized on {self.device_path}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to initialize {{ADAPTER_NAME}}: {str(e)}"
            )

    def cleanup(self) -> OperationResult:
        """
        Clean up the {{ADAPTER_NAME}} interface

        Returns:
            OperationResult: Success/failure with details
        """
        try:
            # TODO: Implement your cleanup logic
            # Example:
            # if self._device_handle:
            #     close_device(self._device_handle)
            #     self._device_handle = None

            self._is_initialized = False
            return OperationResult(
                success=True,
                log="{{ADAPTER_NAME}} cleaned up successfully"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to cleanup {{ADAPTER_NAME}}: {str(e)}"
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

    def send_data(self, data) -> OperationResult:
        """
        Send data via {{ADAPTER_NAME}} interface

        Args:
            data: Data to send (adapt type as needed)

        Returns:
            OperationResult: Success/failure with response data
        """
        if not self.is_ready():
            return OperationResult(
                success=False,
                error="{{ADAPTER_NAME}} not initialized"
            )

        try:
            # TODO: Implement your send logic
            # result = send_via_device(self._device_handle, data)

            return OperationResult(
                success=True,
                data=f"Sent data via {{ADAPTER_NAME}}",
                log=f"Successfully sent {len(str(data))} bytes"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to send data: {str(e)}"
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


# TODO: If you need a mock version for testing, create it here:
class Mock{{ADAPTER_CLASS}}({{ADAPTER_CLASS}}):
    """
    Mock {{ADAPTER_NAME}} adapter for testing without hardware
    """

    def __init__(self, config):
        super().__init__(config)
        self._mock_data_queue = []

    def initialize(self) -> OperationResult:
        """Mock initialization - always succeeds"""
        self._is_initialized = True
        self._device_handle = "mock_handle"
        return OperationResult(
            success=True,
            log=f"Mock {{ADAPTER_NAME}} initialized"
        )

    def send_data(self, data) -> OperationResult:
        """Mock send - stores data for later retrieval"""
        if not self.is_ready():
            return OperationResult(success=False, error="Not initialized")

        # Store data for mock receive
        self._mock_data_queue.append(f"echo_{data}")

        return OperationResult(
            success=True,
            data=f"Mock sent: {data}",
            log=f"Mock {{ADAPTER_NAME}} sent data"
        )

    def receive_data(self, timeout: float = 1.0) -> OperationResult:
        """Mock receive - returns queued data or default"""
        if not self.is_ready():
            return OperationResult(success=False, error="Not initialized")

        if self._mock_data_queue:
            data = self._mock_data_queue.pop(0)
        else:
            data = "mock_default_response"

        return OperationResult(
            success=True,
            data=data,
            log=f"Mock {{ADAPTER_NAME}} received data"
        )