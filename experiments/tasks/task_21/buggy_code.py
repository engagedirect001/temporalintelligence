"""
Task 21: Circuit Breaker with Health Monitoring
Category: Combined — system design + state machine + concurrency bugs
"""
import time
import threading
from enum import Enum, auto
from collections import deque


class CircuitState(Enum):
    CLOSED = auto()      # Normal operation
    OPEN = auto()        # Failing, reject requests
    HALF_OPEN = auto()   # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold=5, success_threshold=3,
                 timeout=30.0, window_size=60.0, time_fn=None):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.window_size = window_size
        self.time_fn = time_fn or time.monotonic
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.failure_times = deque()  # timestamps of recent failures
        self.lock = threading.Lock()
        self.half_open_in_progress = False
    
    def can_execute(self):
        """Check if request should be allowed."""
        with self.lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            if self.state == CircuitState.OPEN:
                now = self.time_fn()
                if now - self.last_failure_time >= self.timeout:
                    # Bug 1: transitions to HALF_OPEN but allows ALL requests through
                    # Should only allow ONE test request
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            
            if self.state == CircuitState.HALF_OPEN:
                # Bug 1 continued: should only allow one request at a time in half-open
                return True
    
    def record_success(self):
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self._transition_to_closed()
            elif self.state == CircuitState.CLOSED:
                # Reset failure tracking on success? 
                # Bug 2: doesn't clear failure_times on success,
                # so old failures within the window still count
                pass
    
    def record_failure(self):
        with self.lock:
            now = self.time_fn()
            
            if self.state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._transition_to_open(now)
                return
            
            if self.state == CircuitState.CLOSED:
                self.failure_times.append(now)
                self._clean_old_failures(now)
                
                # Bug 3: counts total failures in window, but failure_count
                # is separate from failure_times — they go out of sync
                self.failure_count += 1
                
                if len(self.failure_times) >= self.failure_threshold:
                    self._transition_to_open(now)
    
    def _clean_old_failures(self, now):
        window_start = now - self.window_size
        while self.failure_times and self.failure_times[0] < window_start:
            self.failure_times.popleft()
            # Bug 3: decrements failure_count for expired failures
            # but failure_count was also incremented independently
            self.failure_count = max(0, self.failure_count - 1)
    
    def _transition_to_open(self, now):
        self.state = CircuitState.OPEN
        self.last_failure_time = now
        self.success_count = 0
    
    def _transition_to_closed(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.failure_times.clear()
    
    def get_state(self):
        with self.lock:
            return self.state
    
    def execute(self, func, *args, **kwargs):
        """Execute function through circuit breaker."""
        if not self.can_execute():
            raise RuntimeError("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
