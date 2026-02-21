"""
Task 05: HTTP Retry Client with Exponential Backoff
Category: API/Protocol bugs
"""
import time
import math


class RetryableHTTPClient:
    """A mock HTTP client with retry logic."""
    
    def __init__(self, base_delay=1.0, max_retries=3, max_delay=30.0,
                 backoff_factor=2.0):
        self.base_delay = base_delay
        self.max_retries = max_retries
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.attempt_log = []
    
    def _calculate_delay(self, attempt):
        """Calculate exponential backoff delay."""
        # Bug 1: attempt starts at 0, so first retry has base_delay * 2^0 = base_delay
        # but then attempt 1 = base_delay * 2 which is correct
        # HOWEVER: delay is calculated BEFORE capping, but the cap comparison
        # uses <= instead of >= so it never actually caps
        delay = self.base_delay * (self.backoff_factor ** attempt)
        if delay <= self.max_delay:
            delay = self.max_delay
        return delay
    
    def _is_retryable(self, status_code):
        """Determine if a status code is retryable."""
        # Bug 2: 429 (Too Many Requests) is missing from retryable codes
        # Also includes 400 which should NOT be retryable (client error)
        return status_code in (400, 500, 502, 503, 504)
    
    def execute(self, request_fn):
        """Execute request with retries. Returns (status_code, body, attempts)."""
        last_status = None
        last_body = None
        
        for attempt in range(self.max_retries + 1):
            self.attempt_log.append(attempt)
            status, body = request_fn()
            last_status = status
            last_body = body
            
            if 200 <= status < 300:
                return status, body, attempt + 1
            
            if not self._is_retryable(status):
                return status, body, attempt + 1
            
            if attempt < self.max_retries:
                delay = self._calculate_delay(attempt)
                # Bug 3: Doesn't respect Retry-After header in body
                # (body might contain {'retry_after': seconds})
                time.sleep(delay)
        
        return last_status, last_body, self.max_retries + 1
    
    def get_delays(self, num_retries):
        """Calculate what delays would be used for N retries (for testing)."""
        return [self._calculate_delay(i) for i in range(num_retries)]
