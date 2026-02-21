"""
Task 23: Lock-Free Ring Buffer (SPSC)
Category: Hardest — concurrency + data structure + memory ordering
"""
import threading
import time


class SPSCRingBuffer:
    """Single-Producer Single-Consumer lock-free ring buffer.
    Uses modular arithmetic for head/tail positions."""
    
    def __init__(self, capacity):
        # Bug 1: capacity should be power of 2 for modular arithmetic,
        # but we don't enforce it AND the mask is wrong for non-power-of-2
        self.capacity = capacity
        self.mask = capacity - 1  # only correct if capacity is power of 2
        self.buffer = [None] * capacity
        self.head = 0  # next write position (producer)
        self.tail = 0  # next read position (consumer)
        self.write_count = 0
        self.read_count = 0
        self.overflow_count = 0
    
    def _size(self):
        """Current number of items."""
        # Bug 2: this calculation is wrong when head wraps around
        # With mask: (head - tail) & mask, but this is wrong too
        # for non-power-of-2 capacity
        return (self.head - self.tail) & self.mask
    
    def is_full(self):
        # Bug: _size uses broken mask math
        return self._size() == self.capacity - 1
    
    def is_empty(self):
        return self.head == self.tail
    
    def put(self, item):
        """Producer writes item. Returns True if successful."""
        if self.is_full():
            self.overflow_count += 1
            return False
        
        self.buffer[self.head & self.mask] = item
        # Bug 3: no memory barrier — consumer might see updated head
        # before buffer write is visible. In CPython with GIL this is
        # mostly safe, but the real bug is:
        # head increment should use modular arithmetic consistently
        self.head += 1
        self.write_count += 1
        return True
    
    def get(self):
        """Consumer reads item. Returns item or None if empty."""
        if self.is_empty():
            return None
        
        item = self.buffer[self.tail & self.mask]
        self.tail += 1
        self.read_count += 1
        return item
    
    def drain(self):
        """Read all available items."""
        items = []
        while not self.is_empty():
            item = self.get()
            if item is not None:
                items.append(item)
        return items


def run_spsc_test(num_items, capacity):
    """Run producer-consumer test. Returns (produced, consumed, items)."""
    buf = SPSCRingBuffer(capacity)
    consumed = []
    
    def producer():
        for i in range(num_items):
            while not buf.put(i):
                time.sleep(0.0001)  # backoff
    
    def consumer():
        count = 0
        while count < num_items:
            item = buf.get()
            if item is not None:
                consumed.append(item)
                count += 1
            else:
                time.sleep(0.0001)
    
    p = threading.Thread(target=producer)
    c = threading.Thread(target=consumer)
    p.start()
    c.start()
    p.join(timeout=10)
    c.join(timeout=10)
    
    return buf.write_count, buf.read_count, consumed
