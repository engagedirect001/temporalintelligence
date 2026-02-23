import pytest
import threading
import time
from buggy_code import BoundedBuffer, run_producer_consumer


def test_single_producer_consumer():
    """Basic test — should work even with bugs in most cases."""
    produced, consumed = run_producer_consumer(10, 5, 1, 1)
    assert produced == 10
    assert consumed == 10


def test_multiple_consumers_all_items_consumed():
    """With shared condition + notify(), consumers may miss wakeups."""
    produced, consumed = run_producer_consumer(100, 2, 2, 4)
    assert produced == 100
    assert consumed == 100


def test_close_wakes_all_consumers():
    """Bug 2: close() uses notify() not notify_all() — some consumers hang."""
    buf = BoundedBuffer(5)
    results = []
    
    def consumer(cid):
        item = buf.get(timeout=2)
        results.append((cid, item))
    
    consumers = [threading.Thread(target=consumer, args=(i,)) for i in range(4)]
    for c in consumers:
        c.start()
    
    time.sleep(0.2)
    buf.put("only_one")
    time.sleep(0.1)
    buf.close()
    
    for c in consumers:
        c.join(timeout=3)
        assert not c.is_alive(), f"Consumer thread still alive — likely blocked on condition"
    
    got_items = [r for r in results if r[1] is not None]
    got_none = [r for r in results if r[1] is None]
    assert len(got_items) == 1
    assert len(got_none) == 3


def test_timeout_returns_none():
    """Bug 3: timeout doesn't properly return None when buffer stays empty."""
    buf = BoundedBuffer(5)
    start = time.time()
    result = buf.get(timeout=0.3)
    elapsed = time.time() - start
    assert result is None, "Should return None on timeout with empty buffer"
    assert elapsed < 1.0, "Should not hang indefinitely"


def test_buffer_capacity_respected():
    buf = BoundedBuffer(2)
    buf.put("a")
    buf.put("b")
    
    filled = threading.Event()
    
    def try_put():
        filled.set()
        buf.put("c")  # should block
    
    t = threading.Thread(target=try_put)
    t.start()
    filled.wait()
    time.sleep(0.2)
    assert t.is_alive(), "put() should block when buffer is full"
    buf.get()  # free a slot
    t.join(timeout=2)
    assert not t.is_alive()


def test_high_contention():
    """Stress test: many producers and consumers with tiny buffer."""
    for _ in range(3):
        produced, consumed = run_producer_consumer(50, 1, 5, 5)
        assert produced == 50
        assert consumed == 50
