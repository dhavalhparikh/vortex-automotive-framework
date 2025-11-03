"""
CLI Adapter

CLI command execution via serial/SSH with response capture and comparison.
Supports both serial (/dev/tty*) and SSH connections for executing commands
and capturing responses for validation.
"""

import serial
import paramiko
import time
import re
import difflib
from typing import Dict, Any, Optional, List, Union
from framework.core.types import OperationResult
import logging

logger = logging.getLogger(__name__)


class CliAdapter:
    """
    CLI interface adapter

    Executes commands via serial or SSH connections and captures responses
    for comparison with expected data. Ideal for testing CLI interfaces
    on embedded systems, routers, switches, etc.
    """

    def __init__(self, config):
        self.config = config

        # Connection configuration
        self.device_path = config.get('device_path', '/dev/ttyUSB0')
        self.connection_type = config.get('connection_type', 'serial')  # 'serial' or 'ssh'

        # Serial configuration
        self.baudrate = config.get('baudrate', 115200)
        self.timeout = config.get('timeout', 5.0)
        self.bytesize = config.get('bytesize', serial.EIGHTBITS)
        self.parity = config.get('parity', serial.PARITY_NONE)
        self.stopbits = config.get('stopbits', serial.STOPBITS_ONE)

        # SSH configuration
        self.ssh_host = config.get('ssh_host', 'localhost')
        self.ssh_port = config.get('ssh_port', 22)
        self.ssh_username = config.get('ssh_username', 'root')
        self.ssh_password = config.get('ssh_password')
        self.ssh_key_path = config.get('ssh_key_path')

        # CLI behavior configuration
        self.command_timeout = config.get('command_timeout', 10.0)
        self.prompt_pattern = config.get('prompt_pattern', r'[\$#>]\s*$')
        self.login_prompt = config.get('login_prompt', 'login:')
        self.password_prompt = config.get('password_prompt', 'Password:')
        self.command_delay = config.get('command_delay', 0.1)

        # Internal state
        self._is_initialized = False
        self._serial_connection = None
        self._ssh_client = None
        self._ssh_shell = None
        self._last_output = ""

    def initialize(self) -> OperationResult:
        """
        Initialize the CLI interface

        Returns:
            OperationResult: Success/failure with details
        """
        try:
            if self.connection_type == 'serial':
                return self._initialize_serial()
            elif self.connection_type == 'ssh':
                return self._initialize_ssh()
            else:
                return OperationResult(
                    success=False,
                    error=f"Unsupported connection type: {self.connection_type}"
                )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to initialize CLI: {str(e)}"
            )

    def _initialize_serial(self) -> OperationResult:
        """Initialize serial connection"""
        try:
            self._serial_connection = serial.Serial(
                port=self.device_path,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=self.bytesize,
                parity=self.parity,
                stopbits=self.stopbits
            )

            # Clear any existing data
            self._serial_connection.reset_input_buffer()
            self._serial_connection.reset_output_buffer()

            self._is_initialized = True
            return OperationResult(
                success=True,
                log=f"Serial CLI initialized on {self.device_path} @ {self.baudrate}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to initialize serial connection: {str(e)}"
            )

    def _initialize_ssh(self) -> OperationResult:
        """Initialize SSH connection"""
        try:
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect with password or key
            if self.ssh_key_path:
                self._ssh_client.connect(
                    hostname=self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    key_filename=self.ssh_key_path,
                    timeout=self.timeout
                )
            else:
                self._ssh_client.connect(
                    hostname=self.ssh_host,
                    port=self.ssh_port,
                    username=self.ssh_username,
                    password=self.ssh_password,
                    timeout=self.timeout
                )

            # Create interactive shell
            self._ssh_shell = self._ssh_client.invoke_shell()
            self._ssh_shell.settimeout(self.timeout)

            # Wait for initial prompt
            time.sleep(1)
            self._read_until_prompt()

            self._is_initialized = True
            return OperationResult(
                success=True,
                log=f"SSH CLI initialized to {self.ssh_host}:{self.ssh_port}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to initialize SSH connection: {str(e)}"
            )

    def cleanup(self) -> OperationResult:
        """
        Clean up the CLI interface

        Returns:
            OperationResult: Success/failure with details
        """
        try:
            if self._serial_connection and self._serial_connection.is_open:
                self._serial_connection.close()

            if self._ssh_shell:
                self._ssh_shell.close()

            if self._ssh_client:
                self._ssh_client.close()

            self._is_initialized = False
            return OperationResult(
                success=True,
                log="CLI interface cleaned up successfully"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to cleanup CLI: {str(e)}"
            )

    def is_ready(self) -> bool:
        """
        Check if the adapter is ready for operations

        Returns:
            bool: True if ready, False otherwise
        """
        if not self._is_initialized:
            return False

        if self.connection_type == 'serial':
            return self._serial_connection and self._serial_connection.is_open
        elif self.connection_type == 'ssh':
            return self._ssh_client and self._ssh_shell

        return False

    def get_status(self) -> str:
        """
        Get current adapter status

        Returns:
            str: Status description
        """
        if self.is_ready():
            return f"active ({self.connection_type})"
        else:
            return "inactive"

    def execute_command(self, command: str, timeout: float = None) -> OperationResult:
        """
        Execute a command and capture the response

        Args:
            command: Command to execute
            timeout: Command timeout (uses default if None)

        Returns:
            OperationResult: Success/failure with command output
        """
        if not self.is_ready():
            return OperationResult(
                success=False,
                error="CLI not initialized"
            )

        try:
            timeout = timeout or self.command_timeout

            if self.connection_type == 'serial':
                return self._execute_serial_command(command, timeout)
            elif self.connection_type == 'ssh':
                return self._execute_ssh_command(command, timeout)

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to execute command '{command}': {str(e)}"
            )

    def _execute_serial_command(self, command: str, timeout: float) -> OperationResult:
        """Execute command via serial connection"""
        try:
            # Clear buffer
            self._serial_connection.reset_input_buffer()

            # Send command
            cmd_bytes = (command + '\r\n').encode('utf-8')
            self._serial_connection.write(cmd_bytes)
            self._serial_connection.flush()

            # Wait briefly
            time.sleep(self.command_delay)

            # Read response
            output = self._read_serial_until_prompt(timeout)

            # Store last output
            self._last_output = output

            return OperationResult(
                success=True,
                data=output,
                log=f"Executed serial command: {command}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Serial command execution failed: {str(e)}"
            )

    def _execute_ssh_command(self, command: str, timeout: float) -> OperationResult:
        """Execute command via SSH connection"""
        try:
            # Send command
            self._ssh_shell.send(command + '\n')

            # Wait briefly
            time.sleep(self.command_delay)

            # Read response
            output = self._read_ssh_until_prompt(timeout)

            # Store last output
            self._last_output = output

            return OperationResult(
                success=True,
                data=output,
                log=f"Executed SSH command: {command}"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"SSH command execution failed: {str(e)}"
            )

    def _read_serial_until_prompt(self, timeout: float) -> str:
        """Read from serial until prompt is detected"""
        output = ""
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            if self._serial_connection.in_waiting > 0:
                chunk = self._serial_connection.read(self._serial_connection.in_waiting).decode('utf-8', errors='ignore')
                output += chunk

                # Check for prompt
                if re.search(self.prompt_pattern, output.split('\n')[-1]):
                    break
            else:
                time.sleep(0.1)

        return output.strip()

    def _read_ssh_until_prompt(self, timeout: float) -> str:
        """Read from SSH until prompt is detected"""
        output = ""
        start_time = time.time()

        while (time.time() - start_time) < timeout:
            if self._ssh_shell.recv_ready():
                chunk = self._ssh_shell.recv(4096).decode('utf-8', errors='ignore')
                output += chunk

                # Check for prompt
                if re.search(self.prompt_pattern, output.split('\n')[-1]):
                    break
            else:
                time.sleep(0.1)

        return output.strip()

    def _read_until_prompt(self) -> str:
        """Read until prompt (for initialization)"""
        if self.connection_type == 'serial':
            return self._read_serial_until_prompt(self.timeout)
        elif self.connection_type == 'ssh':
            return self._read_ssh_until_prompt(self.timeout)
        return ""

    def send_ssh_command(self, command: str, host: str = None, username: str = None,
                        password: str = None, timeout: float = None) -> OperationResult:
        """
        Execute command via one-shot SSH connection

        Args:
            command: Command to execute
            host: SSH host (uses config default if None)
            username: SSH username (uses config default if None)
            password: SSH password (uses config default if None)
            timeout: Command timeout

        Returns:
            OperationResult: Success/failure with command output
        """
        try:
            # Use defaults if not provided
            host = host or self.ssh_host
            username = username or self.ssh_username
            password = password or self.ssh_password
            timeout = timeout or self.command_timeout

            # Create temporary SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect and execute
            ssh.connect(hostname=host, username=username, password=password, timeout=timeout)
            stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)

            # Get output
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_code = stdout.channel.recv_exit_status()

            ssh.close()

            # Store last output
            self._last_output = output

            return OperationResult(
                success=exit_code == 0,
                data={
                    'output': output,
                    'error': error,
                    'exit_code': exit_code
                },
                log=f"SSH command executed: {command} (exit: {exit_code})"
            )

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"SSH command failed: {str(e)}"
            )

    def capture_output(self, timeout: float = None) -> OperationResult:
        """
        Capture current output from the CLI without sending a command

        Args:
            timeout: Read timeout

        Returns:
            OperationResult: Success/failure with captured output
        """
        if not self.is_ready():
            return OperationResult(
                success=False,
                error="CLI not initialized"
            )

        try:
            timeout = timeout or self.timeout

            if self.connection_type == 'serial':
                output = self._read_serial_until_prompt(timeout)
            elif self.connection_type == 'ssh':
                output = self._read_ssh_until_prompt(timeout)
            else:
                return OperationResult(success=False, error="Invalid connection type")

            self._last_output = output

            return OperationResult(
                success=True,
                data=output,
                log="Output captured successfully"
            )

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to capture output: {str(e)}"
            )

    def compare_output(self, expected: str, actual: str = None,
                      ignore_whitespace: bool = True,
                      ignore_case: bool = False) -> OperationResult:
        """
        Compare expected output with actual output

        Args:
            expected: Expected output string
            actual: Actual output (uses last captured if None)
            ignore_whitespace: Ignore whitespace differences
            ignore_case: Ignore case differences

        Returns:
            OperationResult: Success/failure with comparison details
        """
        try:
            # Use last output if actual not provided
            actual = actual or self._last_output

            if not actual:
                return OperationResult(
                    success=False,
                    error="No actual output available for comparison"
                )

            # Normalize strings if requested
            exp_normalized = expected
            act_normalized = actual

            if ignore_whitespace:
                exp_normalized = re.sub(r'\s+', ' ', exp_normalized.strip())
                act_normalized = re.sub(r'\s+', ' ', act_normalized.strip())

            if ignore_case:
                exp_normalized = exp_normalized.lower()
                act_normalized = act_normalized.lower()

            # Compare
            match = exp_normalized == act_normalized

            # Generate diff if not matching
            diff = ""
            if not match:
                diff_lines = list(difflib.unified_diff(
                    expected.splitlines(keepends=True),
                    actual.splitlines(keepends=True),
                    fromfile='expected',
                    tofile='actual'
                ))
                diff = ''.join(diff_lines)

            return OperationResult(
                success=match,
                data={
                    'match': match,
                    'expected': expected,
                    'actual': actual,
                    'diff': diff,
                    'normalized_expected': exp_normalized,
                    'normalized_actual': act_normalized
                },
                log=f"Output comparison: {'MATCH' if match else 'MISMATCH'}"
            )

        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to compare output: {str(e)}"
            )

    def get_last_output(self) -> str:
        """Get the last captured output"""
        return self._last_output

    def clear_output_buffer(self) -> OperationResult:
        """Clear the output buffer"""
        try:
            if self.connection_type == 'serial' and self._serial_connection:
                self._serial_connection.reset_input_buffer()

            self._last_output = ""

            return OperationResult(
                success=True,
                log="Output buffer cleared"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                error=f"Failed to clear buffer: {str(e)}"
            )


class MockCliAdapter(CliAdapter):
    """
    Mock CLI adapter for testing without actual devices
    """

    def __init__(self, config):
        super().__init__(config)
        self._mock_responses = {}
        self._command_history = []

    def initialize(self) -> OperationResult:
        """Mock initialization - always succeeds"""
        self._is_initialized = True
        return OperationResult(
            success=True,
            log=f"Mock CLI initialized ({self.connection_type})"
        )

    def is_ready(self) -> bool:
        """Mock is always ready when initialized"""
        return self._is_initialized

    def execute_command(self, command: str, timeout: float = None) -> OperationResult:
        """Mock command execution"""
        if not self.is_ready():
            return OperationResult(success=False, error="Not initialized")

        # Store command in history
        self._command_history.append(command)

        # Generate mock response
        if command in self._mock_responses:
            output = self._mock_responses[command]
        else:
            output = f"Mock response for: {command}\nCommand executed successfully.\n$ "

        self._last_output = output

        return OperationResult(
            success=True,
            data=output,
            log=f"Mock CLI executed: {command}"
        )

    def send_ssh_command(self, command: str, host: str = None, username: str = None,
                        password: str = None, timeout: float = None) -> OperationResult:
        """Mock SSH command execution"""
        self._command_history.append(f"SSH: {command}")

        output = f"Mock SSH response for: {command}"
        self._last_output = output

        return OperationResult(
            success=True,
            data={
                'output': output,
                'error': '',
                'exit_code': 0
            },
            log=f"Mock SSH executed: {command}"
        )

    def set_mock_response(self, command: str, response: str):
        """Set mock response for a specific command"""
        self._mock_responses[command] = response

    def get_command_history(self) -> List[str]:
        """Get list of executed commands"""
        return self._command_history.copy()

    def clear_history(self):
        """Clear command history"""
        self._command_history.clear()

    def capture_output(self, timeout: float = None) -> OperationResult:
        """Mock output capture - always succeeds"""
        if not self.is_ready():
            return OperationResult(success=False, error="Not initialized")

        # Mock captured output
        captured = "Mock captured output\n$ "
        self._last_output = captured

        return OperationResult(
            success=True,
            data=captured,
            log="Mock output captured"
        )