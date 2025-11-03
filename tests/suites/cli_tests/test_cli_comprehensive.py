"""
CLI Adapter Comprehensive Tests

Tests for CLI adapter functionality including:
- Command execution
- Output capture and comparison
- Serial and SSH modes
- Mock adapter behavior
"""

from framework.core.test_decorators import auto_configure_test


@auto_configure_test
def test_cli_adapter_initialization(cli_interface):
    """Test CLI adapter initialization"""
    result = cli_interface.initialize()
    assert result.success, f"CLI initialization failed: {result.error}"

    # Verify interface is ready
    assert cli_interface.is_ready(), "CLI interface not ready after initialization"

    # Check status
    status = cli_interface.get_status()
    assert "active" in status, f"Expected 'active' in status, got '{status}'"

    print(f"✅ CLI adapter initialized: {status}")


@auto_configure_test
def test_cli_execute_command(cli_interface):
    """Test basic command execution"""
    # Initialize interface
    init_result = cli_interface.initialize()
    assert init_result.success

    # Execute a simple command
    command = "echo 'Hello, CLI!'"
    result = cli_interface.execute_command(command)
    assert result.success, f"Command execution failed: {result.error}"
    assert result.data is not None, "No output data returned"

    print(f"✅ Command executed: {command}")
    print(f"   Output: {result.data}")


@auto_configure_test
def test_cli_mock_response_setting(cli_interface):
    """Test setting custom mock responses"""
    # Initialize interface
    init_result = cli_interface.initialize()
    assert init_result.success

    # Set a custom mock response
    custom_command = "show version"
    custom_response = "Router Version 1.2.3\nBuild: 20231103\n$ "

    # Mock adapters should have this method
    if hasattr(cli_interface, 'set_mock_response'):
        cli_interface.set_mock_response(custom_command, custom_response)

        # Execute the command
        result = cli_interface.execute_command(custom_command)
        assert result.success
        assert custom_response in result.data

        print(f"✅ Custom mock response working")
        print(f"   Command: {custom_command}")
        print(f"   Response: {result.data}")


@auto_configure_test
def test_cli_output_comparison(cli_interface):
    """Test output comparison functionality"""
    # Initialize interface
    init_result = cli_interface.initialize()
    assert init_result.success

    # Execute command
    command = "echo test"
    result = cli_interface.execute_command(command)
    assert result.success

    # Test exact match
    expected_output = result.data
    comparison = cli_interface.compare_output(expected_output)
    assert comparison.success, "Exact match comparison should succeed"
    assert comparison.data['match'], "Should detect exact match"

    # Test mismatch
    wrong_output = "completely different output"
    comparison = cli_interface.compare_output(wrong_output)
    assert not comparison.data['match'], "Should detect mismatch"
    assert comparison.data['diff'], "Should provide diff for mismatch"

    print(f"✅ Output comparison working")
    print(f"   Match detection: ✓")
    print(f"   Diff generation: ✓")


@auto_configure_test
def test_cli_output_comparison_options(cli_interface):
    """Test output comparison with different options"""
    # Initialize interface
    init_result = cli_interface.initialize()
    assert init_result.success

    # Set a mock response with specific formatting
    test_command = "test output"
    original_output = "  Hello    World  \n  Test    Line  "

    if hasattr(cli_interface, 'set_mock_response'):
        cli_interface.set_mock_response(test_command, original_output)

    # Execute command
    result = cli_interface.execute_command(test_command)
    assert result.success

    # Test whitespace normalization
    expected_normalized = "Hello World Test Line"
    comparison = cli_interface.compare_output(
        expected_normalized,
        ignore_whitespace=True
    )
    assert comparison.data['match'], "Should match with whitespace normalization"

    # Test case insensitivity
    expected_different_case = "hello world test line"
    comparison = cli_interface.compare_output(
        expected_different_case,
        ignore_whitespace=True,
        ignore_case=True
    )
    assert comparison.data['match'], "Should match with case insensitivity"

    print(f"✅ Output comparison options working")
    print(f"   Whitespace normalization: ✓")
    print(f"   Case insensitivity: ✓")


@auto_configure_test
def test_cli_ssh_command_execution(cli_interface):
    """Test SSH command execution"""
    # Initialize interface
    init_result = cli_interface.initialize()
    assert init_result.success

    # Test SSH command (will use mock)
    command = "uptime"
    result = cli_interface.send_ssh_command(command)
    assert result.success, f"SSH command failed: {result.error}"

    # Check result structure
    assert 'output' in result.data, "SSH result should have 'output' field"
    assert 'error' in result.data, "SSH result should have 'error' field"
    assert 'exit_code' in result.data, "SSH result should have 'exit_code' field"

    print(f"✅ SSH command execution working")
    print(f"   Command: {command}")
    print(f"   Exit code: {result.data['exit_code']}")
    print(f"   Output: {result.data['output']}")


@auto_configure_test
def test_cli_command_history(cli_interface):
    """Test command history tracking (mock adapter feature)"""
    # Initialize interface
    init_result = cli_interface.initialize()
    assert init_result.success

    # Execute several commands
    commands = ["ls -la", "pwd", "whoami"]

    for cmd in commands:
        result = cli_interface.execute_command(cmd)
        assert result.success

    # Check history (if available)
    if hasattr(cli_interface, 'get_command_history'):
        history = cli_interface.get_command_history()
        assert len(history) >= len(commands), "History should contain executed commands"

        # Check that our commands are in history
        for cmd in commands:
            assert cmd in history, f"Command '{cmd}' should be in history"

        print(f"✅ Command history working")
        print(f"   Commands executed: {len(commands)}")
        print(f"   History entries: {len(history)}")
        print(f"   History: {history}")


@auto_configure_test
def test_cli_output_capture(cli_interface):
    """Test output capture without command execution"""
    # Initialize interface
    init_result = cli_interface.initialize()
    assert init_result.success

    # Execute a command first to have some output
    result = cli_interface.execute_command("echo capture test")
    assert result.success

    # Test capturing current output
    capture_result = cli_interface.capture_output()
    assert capture_result.success, f"Output capture failed: {capture_result.error}"
    assert capture_result.data is not None, "Captured output should not be None"

    # Verify we can get last output
    last_output = cli_interface.get_last_output()
    assert last_output, "Should have last output available"

    print(f"✅ Output capture working")
    print(f"   Captured: {len(capture_result.data)} characters")
    print(f"   Last output: {len(last_output)} characters")


@auto_configure_test
def test_cli_buffer_management(cli_interface):
    """Test output buffer clearing"""
    # Initialize interface
    init_result = cli_interface.initialize()
    assert init_result.success

    # Execute command to populate buffer
    result = cli_interface.execute_command("echo buffer test")
    assert result.success

    # Verify we have output
    output_before = cli_interface.get_last_output()
    assert output_before, "Should have output before clearing"

    # Clear buffer
    clear_result = cli_interface.clear_output_buffer()
    assert clear_result.success, f"Buffer clear failed: {clear_result.error}"

    # Verify buffer is cleared
    output_after = cli_interface.get_last_output()
    assert not output_after, "Output should be cleared"

    print(f"✅ Buffer management working")
    print(f"   Before clear: {len(output_before)} characters")
    print(f"   After clear: {len(output_after)} characters")


@auto_configure_test
def test_cli_error_handling(cli_interface):
    """Test CLI error handling"""
    # Test operations without initialization
    result = cli_interface.execute_command("test")
    assert not result.success, "Should fail when not initialized"
    assert "not initialized" in result.error.lower()

    result = cli_interface.capture_output()
    assert not result.success, "Should fail when not initialized"

    # Initialize and test invalid operations
    init_result = cli_interface.initialize()
    assert init_result.success

    # Test comparison without output
    if hasattr(cli_interface, 'clear_history'):
        cli_interface.clear_history()

    cli_interface.clear_output_buffer()
    comparison = cli_interface.compare_output("test")
    assert not comparison.success, "Should fail when no output available"

    print(f"✅ Error handling working")
    print(f"   Uninitialized operations: ✓")
    print(f"   Invalid operations: ✓")


@auto_configure_test
def test_cli_cleanup(cli_interface):
    """Test CLI interface cleanup"""
    # Initialize first
    init_result = cli_interface.initialize()
    assert init_result.success

    # Verify it's ready
    assert cli_interface.is_ready()

    # Cleanup
    cleanup_result = cli_interface.cleanup()
    assert cleanup_result.success, f"CLI cleanup failed: {cleanup_result.error}"

    # Verify it's no longer ready
    assert not cli_interface.is_ready(), "Interface should not be ready after cleanup"

    print(f"✅ CLI cleanup working")