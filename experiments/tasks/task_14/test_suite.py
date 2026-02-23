import pytest
from buggy_code import SlidingWindowRateLimiter


class MockTime:
    def __init__(self, start=0.0):
        self._now = start
    def __call__(self):
        return self._now
    def advance(self, s):
        self._now += s


def test_basic_allow():
    clock = MockTime()
    rl = SlidingWindowRateLimiter(3, 10.0, time_fn=clock)
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is True
    assert rl.allow() is False


def test_window_slides():
    clock = MockTime()
    rl = SlidingWindowRateLimiter(2, 5.0, time_fn=clock)
    
    assert rl.allow() is True   # t=0
    clock.advance(2)
    assert rl.allow() is True   # t=2
    assert rl.allow() is False  # t=2, at limit
    
    clock.advance(3.5)  # t=5.5 — first request at t=0 should have expired
    assert rl.allow() is True, "Window should have slid past first request"


def test_exact_boundary():
    """Bug 1: request at exactly window_start should be expired."""
    clock = MockTime(start=100.0)
    rl = SlidingWindowRateLimiter(1, 10.0, time_fn=clock)
    
    assert rl.allow() is True  # t=100
    clock.advance(10.0)  # t=110, exactly at boundary
    
    # Request at t=100 is exactly 10s ago = window_seconds
    # It should be expired, allowing a new request
    assert rl.allow() is True, \
        "Request at exact window boundary should be expired"


def test_retry_after():
    clock = MockTime(start=0.0)
    rl = SlidingWindowRateLimiter(2, 10.0, time_fn=clock)
    
    rl.allow()  # t=0
    clock.advance(3)
    rl.allow()  # t=3
    
    # Now at limit. Retry should be when first request expires
    retry = rl.get_retry_after()
    assert retry == pytest.approx(7.0, abs=0.1), \
        f"Should wait ~7s for t=0 request to expire, got {retry}"


def test_multiple_clients():
    clock = MockTime()
    rl = SlidingWindowRateLimiter(1, 10.0, time_fn=clock)
    
    assert rl.allow("alice") is True
    assert rl.allow("bob") is True
    assert rl.allow("alice") is False
    assert rl.allow("bob") is False


def test_remaining():
    clock = MockTime()
    rl = SlidingWindowRateLimiter(5, 10.0, time_fn=clock)
    
    assert rl.get_remaining() == 5
    rl.allow()
    assert rl.get_remaining() == 4
    rl.allow()
    rl.allow()
    assert rl.get_remaining() == 2


def test_reset():
    clock = MockTime()
    rl = SlidingWindowRateLimiter(1, 10.0, time_fn=clock)
    rl.allow()
    assert rl.allow() is False
    rl.reset()
    assert rl.allow() is True
