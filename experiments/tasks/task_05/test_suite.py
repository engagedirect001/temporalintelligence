import pytest
from unittest.mock import patch
from buggy_code import RetryableHTTPClient


def test_success_no_retry():
    client = RetryableHTTPClient()
    status, body, attempts = client.execute(lambda: (200, "ok"))
    assert status == 200
    assert attempts == 1


def test_exponential_backoff_delays():
    """Bug 1: delay cap logic is inverted — delays are always max_delay."""
    client = RetryableHTTPClient(base_delay=1.0, max_delay=30.0, backoff_factor=2.0)
    delays = client.get_delays(4)
    # Expected: [1.0, 2.0, 4.0, 8.0]
    assert delays[0] == pytest.approx(1.0), f"First delay should be 1.0, got {delays[0]}"
    assert delays[1] == pytest.approx(2.0), f"Second delay should be 2.0, got {delays[1]}"
    assert delays[2] == pytest.approx(4.0), f"Third delay should be 4.0, got {delays[2]}"
    # All should be <= max_delay
    for d in delays:
        assert d <= 30.0, f"Delay {d} exceeds max_delay 30.0"


def test_429_is_retryable():
    """Bug 2: 429 Too Many Requests should be retried."""
    client = RetryableHTTPClient(max_retries=2, base_delay=0.001)
    call_count = [0]
    
    def mock_request():
        call_count[0] += 1
        if call_count[0] < 3:
            return 429, {"retry_after": 1}
        return 200, "ok"
    
    with patch('buggy_code.time.sleep'):
        status, body, attempts = client.execute(mock_request)
    
    assert status == 200, f"Should retry 429 and eventually succeed, got {status}"
    assert attempts == 3


def test_400_not_retryable():
    """Bug 2: 400 Bad Request should NOT be retried."""
    client = RetryableHTTPClient(max_retries=3, base_delay=0.001)
    call_count = [0]
    
    def mock_request():
        call_count[0] += 1
        return 400, "bad request"
    
    status, body, attempts = client.execute(mock_request)
    assert attempts == 1, f"400 should not be retried, but got {attempts} attempts"


def test_delay_cap():
    """Delays should never exceed max_delay."""
    client = RetryableHTTPClient(base_delay=1.0, max_delay=5.0, backoff_factor=3.0)
    delays = client.get_delays(10)
    for i, d in enumerate(delays):
        assert d <= 5.0, f"Delay at attempt {i} is {d}, exceeds max 5.0"


def test_retry_exhaustion():
    client = RetryableHTTPClient(max_retries=2, base_delay=0.001)
    with patch('buggy_code.time.sleep'):
        status, body, attempts = client.execute(lambda: (500, "error"))
    assert attempts == 3  # initial + 2 retries
    assert status == 500


def test_503_is_retryable():
    client = RetryableHTTPClient(max_retries=1, base_delay=0.001)
    calls = [0]
    def req():
        calls[0] += 1
        if calls[0] == 1:
            return 503, "unavailable"
        return 200, "ok"
    
    with patch('buggy_code.time.sleep'):
        status, body, attempts = client.execute(req)
    assert status == 200
    assert attempts == 2
