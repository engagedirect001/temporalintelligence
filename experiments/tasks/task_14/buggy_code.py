"""
Task 14: Rate Limiter with Sliding Window
Category: System design bugs
"""
import time
import threading
from collections import defaultdict


class SlidingWindowRateLimiter:
    """Rate limiter using sliding window log algorithm."""
    
    def __init__(self, max_requests, window_seconds, time_fn=None):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.time_fn = time_fn or time.monotonic
        self.request_logs = defaultdict(list)  # client_id -> [timestamps]
        self.lock = threading.Lock()
    
    def allow(self, client_id="default"):
        """Return True if request is allowed, False if rate limited."""
        now = self.time_fn()
        window_start = now - self.window_seconds
        
        with self.lock:
            log = self.request_logs[client_id]
            
            # Remove expired entries
            # Bug 1: uses < instead of <= so entries exactly at window boundary
            # are kept, making the window effectively window_seconds + epsilon
            while log and log[0] < window_start:
                log.pop(0)
            
            if len(log) < self.max_requests:
                log.append(now)
                return True
            else:
                # Bug 2: should still record the denied request timestamp?
                # No — but the real bug is we DON'T return the denial,
                # we fall through
                return False
    
    def get_retry_after(self, client_id="default"):
        """Return seconds until next request would be allowed."""
        now = self.time_fn()
        
        with self.lock:
            log = self.request_logs.get(client_id, [])
            if len(log) < self.max_requests:
                return 0.0
            
            # Bug 3: off by one — oldest relevant request determines when
            # the window slides enough. Should look at log[0], but after
            # cleanup, log[0] is the oldest NON-expired entry.
            # The retry time should be: log[0] + window_seconds - now
            # But we need to account for the entry that will expire FIRST
            oldest = log[0]
            return oldest + self.window_seconds - now
    
    def reset(self, client_id=None):
        with self.lock:
            if client_id:
                self.request_logs.pop(client_id, None)
            else:
                self.request_logs.clear()
    
    def get_remaining(self, client_id="default"):
        """Return number of remaining requests in current window."""
        now = self.time_fn()
        window_start = now - self.window_seconds
        
        with self.lock:
            log = self.request_logs.get(client_id, [])
            # Bug: doesn't clean up expired entries before counting
            # (uses same < bug as allow())
            active = [t for t in log if t >= window_start]
            return max(0, self.max_requests - len(active))
