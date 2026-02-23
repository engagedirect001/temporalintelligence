import pytest
import threading
import time
from buggy_code import CircuitBreaker, CircuitState


class MockTime:
    def __init__(self, start=0.0):
        self._now = start
    def __call__(self):
        return self._now
    def advance(self, s):
        self._now += s


def test_starts_closed():
    cb = CircuitBreaker()
    assert cb.get_state() == CircuitState.CLOSED


def test_opens_after_threshold():
    clock = MockTime()
    cb = CircuitBreaker(failure_threshold=3, time_fn=clock)
    
    for _ in range(3):
        cb.record_failure()
    
    assert cb.get_state() == CircuitState.OPEN


def test_half_open_after_timeout():
    clock = MockTime()
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0, time_fn=clock)
    
    for _ in range(3):
        cb.record_failure()
    assert cb.get_state() == CircuitState.OPEN
    
    clock.advance(11)
    assert cb.can_execute() is True
    assert cb.get_state() == CircuitState.HALF_OPEN


def test_half_open_limits_requests():
    """Bug 1: HALF_OPEN should only allow one test request at a time."""
    clock = MockTime()
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0, 
                        success_threshold=2, time_fn=clock)
    
    for _ in range(3):
        cb.record_failure()
    
    clock.advance(11)
    
    # First request should be allowed
    assert cb.can_execute() is True
    
    # While first is in progress, second should be blocked
    # (simulating concurrent requests in half-open state)
    assert cb.can_execute() is False, \
        "HALF_OPEN should only allow one request at a time"


def test_closes_after_success_threshold():
    clock = MockTime()
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0,
                        success_threshold=2, time_fn=clock)
    
    for _ in range(3):
        cb.record_failure()
    
    clock.advance(11)
    cb.can_execute()  # transitions to half-open
    
    cb.record_success()
    assert cb.get_state() == CircuitState.HALF_OPEN
    cb.record_success()
    assert cb.get_state() == CircuitState.CLOSED


def test_half_open_failure_reopens():
    clock = MockTime()
    cb = CircuitBreaker(failure_threshold=3, timeout=10.0, time_fn=clock)
    
    for _ in range(3):
        cb.record_failure()
    
    clock.advance(11)
    cb.can_execute()  # half-open
    cb.record_failure()
    assert cb.get_state() == CircuitState.OPEN


def test_old_failures_expire():
    """Bug 2: successes should help reset failure tracking within window."""
    clock = MockTime()
    cb = CircuitBreaker(failure_threshold=5, window_size=60.0, time_fn=clock)
    
    # 3 failures
    for _ in range(3):
        cb.record_failure()
        clock.advance(1)
    
    # Some successes
    for _ in range(10):
        cb.record_success()
        clock.advance(1)
    
    # 2 more failures (total 5 but old ones should have decayed importance)
    # Actually, within 60s window, all 5 still count without success clearing
    # The point: successes in CLOSED state should clear the failure_times
    clock.advance(58)  # now old failures are ~70s ago, outside window
    
    cb.record_failure()
    cb.record_failure()
    
    # Should NOT be open — old failures should have expired
    assert cb.get_state() == CircuitState.CLOSED, \
        "Old failures outside window should not count"


def test_execute_success():
    cb = CircuitBreaker()
    result = cb.execute(lambda: 42)
    assert result == 42


def test_execute_failure():
    cb = CircuitBreaker(failure_threshold=1)
    with pytest.raises(ValueError):
        cb.execute(lambda: (_ for _ in ()).throw(ValueError("boom")))
    
    assert cb.get_state() == CircuitState.OPEN
    
    with pytest.raises(RuntimeError, match="OPEN"):
        cb.execute(lambda: 42)
