"""
Task 07: LRU Cache with TTL Expiration
Category: System design bugs
"""
import time
from collections import OrderedDict
from threading import Lock


class TTLCache:
    """Thread-safe LRU cache with per-key TTL."""
    
    def __init__(self, capacity, default_ttl=60.0, time_fn=None):
        self.capacity = capacity
        self.default_ttl = default_ttl
        self.time_fn = time_fn or time.monotonic
        self.cache = OrderedDict()  # key -> (value, expire_time)
        self.lock = Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key):
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            value, expire_time = self.cache[key]
            
            if self.time_fn() > expire_time:
                # Expired — remove and return None
                del self.cache[key]
                self.misses += 1
                return None
            
            # Bug 1: move_to_end should use last=True to mark as recently used
            # but uses last=False which moves it to LEAST recently used
            self.cache.move_to_end(key, last=False)
            self.hits += 1
            return value
    
    def put(self, key, value, ttl=None):
        ttl = ttl if ttl is not None else self.default_ttl
        expire_time = self.time_fn() + ttl
        
        with self.lock:
            if key in self.cache:
                self.cache[key] = (value, expire_time)
                self.cache.move_to_end(key, last=True)
            else:
                if len(self.cache) >= self.capacity:
                    # Bug 2: Evicts most recently used instead of least recently used
                    # when there are expired entries that should be evicted first
                    self.cache.popitem(last=False)
                self.cache[key] = (value, expire_time)
    
    def _evict_expired(self):
        """Remove all expired entries. Bug 3: This method exists but is never called."""
        now = self.time_fn()
        expired = [k for k, (v, exp) in self.cache.items() if now > exp]
        for k in expired:
            del self.cache[k]
    
    def size(self):
        with self.lock:
            return len(self.cache)
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0
