from framework.core.test_decorators import auto_configure_test

@auto_configure_test
def test_mock_adapter_can_loopback(can_interface):
    # Init the mock can adapter
    result = can_interface.initialize()
    assert result.success

    # Send a CAN message
    arb_id = 123
    tx_msg = [1, 2, 3, 45, 67]
    result = can_interface.send_message(arb_id, tx_msg)
    assert result.success

    # Loopback test - receive the message
    arb_id_expected = arb_id + 8 # loopback increments arb_id by 8
    rx_expected_msg = [2, 3, 4, 46, 68] # loopback increments the data
    rx_msg = can_interface.receive_message()
    assert rx_msg is not None
    assert rx_expected_msg == rx_msg.data
    assert arb_id_expected == rx_msg.arbitration_id

@auto_configure_test
def test_mock_adapter_serial_loopback(serial_interface):
    # Init the mock gpio adapter
    result = serial_interface.initialize()
    assert result.success

    # Write data to the interface
    tx_data = b"Serial loopback!"
    result = serial_interface.write(tx_data)
    assert result.success

    # Loopback test - receive message
    rx_data = serial_interface.read(len(tx_data))
    assert rx_data is not None
    assert rx_data == tx_data
