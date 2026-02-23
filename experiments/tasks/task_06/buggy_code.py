"""
Task 06: Running Statistics Calculator (Welford's Algorithm)
Category: Math/Numerical bugs
"""
import math


class RunningStats:
    """Online computation of mean, variance, and standard deviation."""
    
    def __init__(self):
        self.n = 0
        self.mean = 0.0
        self.M2 = 0.0  # sum of squares of differences from current mean
        self.min_val = float('inf')
        self.max_val = float('-inf')
    
    def update(self, x):
        self.n += 1
        # Bug 1: delta should use OLD mean, but mean is updated before delta2
        delta = x - self.mean
        self.mean += delta / self.n
        # Bug 2: delta2 should use NEW mean, which it does, but the formula
        # for M2 is wrong — should be delta * delta2, not delta * delta
        delta2 = x - self.mean
        self.M2 += delta * delta  # Bug: should be delta * delta2
        
        self.min_val = min(self.min_val, x)
        self.max_val = max(self.max_val, x)
    
    def variance(self, ddof=0):
        """Population variance (ddof=0) or sample variance (ddof=1)."""
        if self.n < ddof + 1:
            return float('nan')
        # Bug 3: uses self.n instead of (self.n - ddof)
        return self.M2 / self.n
    
    def stddev(self, ddof=0):
        return math.sqrt(self.variance(ddof))
    
    def get_mean(self):
        if self.n == 0:
            return float('nan')
        return self.mean
    
    def merge(self, other):
        """Merge another RunningStats into this one."""
        if other.n == 0:
            return
        if self.n == 0:
            self.n = other.n
            self.mean = other.mean
            self.M2 = other.M2
            self.min_val = other.min_val
            self.max_val = other.max_val
            return
        
        combined_n = self.n + other.n
        delta = other.mean - self.mean
        combined_mean = (self.n * self.mean + other.n * other.mean) / combined_n
        # Parallel algorithm for M2
        combined_M2 = self.M2 + other.M2 + delta ** 2 * self.n * other.n / combined_n
        
        self.n = combined_n
        self.mean = combined_mean
        self.M2 = combined_M2
        self.min_val = min(self.min_val, other.min_val)
        self.max_val = max(self.max_val, other.max_val)
