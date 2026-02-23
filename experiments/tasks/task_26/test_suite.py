import pytest
from buggy_code import StreamMultiplexer, StreamState, Frame, Stream


def test_create_stream():
    mux = StreamMultiplexer()
    sid = mux.create_stream()
    assert sid == 1
    assert mux.streams[sid].state == StreamState.OPEN


def test_stream_ids_odd():
    """Bug 1: client stream IDs must be odd (1, 3, 5, ...)."""
    mux = StreamMultiplexer()
    s1 = mux.create_stream()
    s2 = mux.create_stream()
    s3 = mux.create_stream()
    
    assert s1 % 2 == 1, f"Stream ID {s1} should be odd"
    assert s2 % 2 == 1, f"Stream ID {s2} should be odd"
    assert s3 % 2 == 1, f"Stream ID {s3} should be odd"
    assert s1 != s2 != s3


def test_send_headers_end_stream():
    """Bug 2: END_STREAM on headers should be HALF_CLOSED_LOCAL, not CLOSED."""
    mux = StreamMultiplexer()
    sid = mux.create_stream()
    
    mux.send_headers(sid, {"method": "GET", "path": "/"}, end_stream=True)
    
    stream = mux.streams[sid]
    assert stream.state == StreamState.HALF_CLOSED_LOCAL, \
        f"Expected HALF_CLOSED_LOCAL after sending headers with END_STREAM, got {stream.state}"


def test_send_headers_then_receive():
    """After sending END_STREAM, should still be able to receive response."""
    mux = StreamMultiplexer()
    sid = mux.create_stream()
    
    mux.send_headers(sid, {"method": "GET"}, end_stream=True)
    
    # Should still be readable (HALF_CLOSED_LOCAL means we can still receive)
    response = Frame(sid, "HEADERS", b"200 OK")
    mux.receive_frame(response)
    
    data = Frame(sid, "DATA", b"response body", {"END_STREAM"})
    mux.receive_frame(data)
    
    assert mux.streams[sid].recv_buffer == b"response body"
    assert mux.streams[sid].state == StreamState.CLOSED


def test_flow_control_connection_window():
    """Bug 3: should check connection window before sending."""
    mux = StreamMultiplexer(initial_window=100)
    
    s1 = mux.create_stream()
    s2 = mux.create_stream()
    
    # Send 80 bytes on stream 1 (stream window=100, conn window=100)
    result1 = mux.send_data(s1, b"x" * 80)
    assert result1 is True
    
    # Connection window now only has 20 bytes left
    # Stream 2 has full 100 byte stream window, but connection is limited
    result2 = mux.send_data(s2, b"x" * 50)
    assert result2 is False, \
        "Should fail: connection window only has 20 bytes left"


def test_send_data_basic():
    mux = StreamMultiplexer()
    sid = mux.create_stream()
    mux.send_data(sid, b"hello")
    assert len(mux.outbound_queue) == 1


def test_receive_data():
    mux = StreamMultiplexer()
    sid = mux.create_stream()
    
    frame = Frame(sid, "DATA", b"incoming data")
    mux.receive_frame(frame)
    assert mux.streams[sid].recv_buffer == b"incoming data"


def test_rst_stream():
    mux = StreamMultiplexer()
    sid = mux.create_stream()
    
    frame = Frame(sid, "RST_STREAM", b"")
    mux.receive_frame(frame)
    assert mux.streams[sid].state == StreamState.CLOSED


def test_priority_ordering():
    mux = StreamMultiplexer()
    s1 = mux.create_stream(priority=100)
    s2 = mux.create_stream(priority=1)
    
    mux.send_data(s1, b"low priority")
    mux.send_data(s2, b"high priority")
    
    ordered = mux.get_prioritized_queue()
    assert ordered[0].stream_id == s2
