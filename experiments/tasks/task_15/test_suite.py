import pytest
import threading
import time
from buggy_code import ConcurrentPriorityQueue


def test_priority_order():
    pq = ConcurrentPriorityQueue()
    pq.put("low", priority=10)
    pq.put("high", priority=1)
    pq.put("mid", priority=5)
    assert pq.get(timeout=1) == "high"
    assert pq.get(timeout=1) == "mid"
    assert pq.get(timeout=1) == "low"


def test_fifo_within_priority():
    pq = ConcurrentPriorityQueue()
    pq.put("first", priority=1)
    pq.put("second", priority=1)
    pq.put("third", priority=1)
    assert pq.get(timeout=1) == "first"
    assert pq.get(timeout=1) == "second"
    assert pq.get(timeout=1) == "third"


def test_cancel():
    pq = ConcurrentPriorityQueue()
    s1 = pq.put("a", priority=1)
    s2 = pq.put("b", priority=2)
    pq.cancel(s1)
    result = pq.get(timeout=1)
    assert result == "b"


def test_cancel_with_timeout():
    """Bug 1+2: cancelling items doesn't adjust timeout. If all items are
    cancelled, get() should time out, not hang."""
    pq = ConcurrentPriorityQueue()
    s1 = pq.put("a", priority=1)
    pq.cancel(s1)
    
    with pytest.raises(TimeoutError):
        pq.get(timeout=0.5)


def test_concurrent_producers_consumers():
    pq = ConcurrentPriorityQueue()
    results = []
    num_items = 50
    
    def producer():
        for i in range(num_items):
            pq.put(i, priority=i)
    
    def consumer():
        for _ in range(num_items):
            try:
                item = pq.get(timeout=2)
                results.append(item)
            except TimeoutError:
                break
    
    p = threading.Thread(target=producer)
    c = threading.Thread(target=consumer)
    p.start()
    c.start()
    p.join()
    c.join(timeout=5)
    
    assert not c.is_alive()
    assert len(results) == num_items


def test_size_with_cancellation():
    pq = ConcurrentPriorityQueue()
    s1 = pq.put("a", 1)
    s2 = pq.put("b", 2)
    pq.cancel(s1)
    assert pq.size() == 1


def test_timeout_on_empty():
    pq = ConcurrentPriorityQueue()
    start = time.monotonic()
    with pytest.raises(TimeoutError):
        pq.get(timeout=0.3)
    elapsed = time.monotonic() - start
    assert elapsed < 1.0, "Should timeout promptly"


def test_get_blocks_until_put():
    pq = ConcurrentPriorityQueue()
    result = [None]
    
    def getter():
        result[0] = pq.get(timeout=2)
    
    t = threading.Thread(target=getter)
    t.start()
    time.sleep(0.1)
    pq.put("delayed", priority=1)
    t.join(timeout=2)
    assert result[0] == "delayed"
