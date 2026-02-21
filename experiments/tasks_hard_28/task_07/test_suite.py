import pytest
from buggy_code import TTLCache


class MockTime:
    def __init__(self, start=0.0):
        self._now = start
    def __call__(self):
        return self._now
    def advance(self, seconds):
        self._now += seconds


def test_basic_put_get():
    clock = MockTime()
    cache = TTLCache(capacity=3, default_ttl=10.0, time_fn=clock)
    cache.put("a", 1)
    assert cache.get("a") == 1


def test_ttl_expiration():
    clock = MockTime()
    cache = TTLCache(capacity=3, default_ttl=5.0, time_fn=clock)
    cache.put("a", 1)
    clock.advance(6)
    assert cache.get("a") is None


def test_lru_eviction_order():
    """Bug 1: get() moves item to FRONT (LRU position) instead of BACK (MRU).
    So getting an item makes it the NEXT to be evicted."""
    clock = MockTime()
    cache = TTLCache(capacity=3, default_ttl=100.0, time_fn=clock)
    
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    
    # Access "a" — should become most recently used (last to evict)
    cache.get("a")
    
    # Add "d" — should evict least recently used ("b")
    cache.put("d", 4)
    
    assert cache.get("b") is None, "b should be evicted (LRU)"
    assert cache.get("a") is not None, "a was accessed recently, should NOT be evicted"
    assert cache.get("c") is not None, "c should still exist"
    assert cache.get("d") is not None, "d was just added"


def test_evict_expired_before_valid():
    """Bug 2: Should evict expired entries before evicting valid LRU entries."""
    clock = MockTime()
    cache = TTLCache(capacity=2, default_ttl=5.0, time_fn=clock)
    
    cache.put("a", 1, ttl=3.0)
    cache.put("b", 2, ttl=100.0)
    
    clock.advance(4)  # "a" is now expired
    
    # Adding "c" should evict expired "a", not valid "b"
    cache.put("c", 3)
    
    assert cache.get("b") == 2, "b should not be evicted — a was expired"
    assert cache.get("c") == 3, "c was just added"


def test_capacity_respected():
    clock = MockTime()
    cache = TTLCache(capacity=2, default_ttl=100.0, time_fn=clock)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    assert cache.size() == 2


def test_update_existing_key():
    clock = MockTime()
    cache = TTLCache(capacity=2, default_ttl=100.0, time_fn=clock)
    cache.put("a", 1)
    cache.put("a", 2)
    assert cache.get("a") == 2
    assert cache.size() == 1


def test_hit_miss_counts():
    clock = MockTime()
    cache = TTLCache(capacity=5, default_ttl=100.0, time_fn=clock)
    cache.put("a", 1)
    cache.get("a")
    cache.get("b")
    assert cache.hits == 1
    assert cache.misses == 1
