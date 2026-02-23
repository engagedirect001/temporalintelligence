import pytest
from buggy_code import TCPConnection, TCPState


def test_normal_client_flow():
    conn = TCPConnection()
    conn.connect()
    assert conn.state == TCPState.SYN_SENT
    conn.receive_syn_ack()
    assert conn.state == TCPState.ESTABLISHED
    conn.close()
    assert conn.state == TCPState.FIN_WAIT_1
    conn.receive_ack()
    assert conn.state == TCPState.FIN_WAIT_2
    conn.receive_fin()
    assert conn.state == TCPState.TIME_WAIT
    conn.timeout()
    assert conn.state == TCPState.CLOSED


def test_normal_server_flow():
    conn = TCPConnection()
    conn.listen()
    conn.receive_syn()
    assert conn.state == TCPState.SYN_RECEIVED
    conn.receive_ack()
    assert conn.state == TCPState.ESTABLISHED


def test_passive_close():
    """Server receives FIN, sends FIN, receives ACK -> CLOSED.
    Bug 1: LAST_ACK + ACK should transition to CLOSED."""
    conn = TCPConnection()
    conn.listen()
    conn.receive_syn()
    conn.receive_ack()
    assert conn.state == TCPState.ESTABLISHED
    
    conn.receive_fin()
    assert conn.state == TCPState.CLOSE_WAIT
    conn.close()
    assert conn.state == TCPState.LAST_ACK
    conn.receive_ack()
    assert conn.state == TCPState.CLOSED


def test_close_from_listen():
    """Bug 2: Should be able to close a listening socket."""
    conn = TCPConnection()
    conn.listen()
    assert conn.state == TCPState.LISTEN
    conn.close()  # should not raise
    assert conn.state == TCPState.CLOSED


def test_simultaneous_close():
    """Bug 3: FIN_WAIT_1 + FIN should go to CLOSING, not TIME_WAIT."""
    conn = TCPConnection()
    conn.connect()
    conn.receive_syn_ack()
    conn.close()
    assert conn.state == TCPState.FIN_WAIT_1
    
    conn.receive_fin()  # simultaneous close
    assert conn.state == TCPState.CLOSING, \
        f"Expected CLOSING, got {conn.state} (FIN_WAIT_1 + FIN should be CLOSING)"
    
    conn.receive_ack()
    assert conn.state == TCPState.TIME_WAIT


def test_send_data_only_when_established():
    conn = TCPConnection()
    with pytest.raises(ConnectionError):
        conn.send_data("hello")
    
    conn.connect()
    conn.receive_syn_ack()
    conn.send_data("hello")  # should work
    assert conn.send_buffer == ["hello"]


def test_simultaneous_open():
    conn = TCPConnection()
    conn.connect()
    assert conn.state == TCPState.SYN_SENT
    conn.receive_syn()
    assert conn.state == TCPState.SYN_RECEIVED
    conn.receive_ack()
    assert conn.state == TCPState.ESTABLISHED
