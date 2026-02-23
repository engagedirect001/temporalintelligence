"""
Task 02: Producer-Consumer Queue with Bounded Buffer
Category: Concurrency bugs
"""
import threading
import time
from collections import deque


class BoundedBuffer:
    def __init__(self, capacity):
        self.capacity = capacity
        self.buffer = deque()
        self.lock = threading.Lock()
        # Bug 1: using the same condition for both not-full and not-empty
        # causes missed wakeups
        self.condition = threading.Condition(self.lock)
        self.closed = False
        self.produced_count = 0
        self.consumed_count = 0
    
    def put(self, item):
        with self.condition:
            while len(self.buffer) >= self.capacity:
                if self.closed:
                    return False
                self.condition.wait()
            if self.closed:
                return False
            self.buffer.append(item)
            self.produced_count += 1
            # Bug 2: notify() instead of notify_all() — with shared condition,
            # might wake a producer instead of consumer
            self.condition.notify()
            return True
    
    def get(self, timeout=None):
        with self.condition:
            while len(self.buffer) == 0:
                if self.closed:
                    return None
                self.condition.wait(timeout=timeout)
                # Bug 3: after timeout, doesn't check if we actually timed out
                # vs spurious wakeup — if buffer still empty AND timed out, should return None
                if len(self.buffer) == 0 and self.closed:
                    return None
            item = self.buffer.popleft()
            self.consumed_count += 1
            self.condition.notify()
            return item
    
    def close(self):
        with self.condition:
            self.closed = True
            # Bug 2 again: should be notify_all
            self.condition.notify()


def run_producer_consumer(num_items, buffer_size, num_producers, num_consumers):
    """Run a producer-consumer workload and return (produced, consumed) counts."""
    buf = BoundedBuffer(buffer_size)
    items_per_producer = num_items // num_producers
    results = []
    
    def producer(pid):
        for i in range(items_per_producer):
            buf.put(f"p{pid}-{i}")
    
    def consumer():
        local_items = []
        while True:
            item = buf.get(timeout=0.5)
            if item is None:
                break
            local_items.append(item)
        results.extend(local_items)
    
    producers = [threading.Thread(target=producer, args=(i,)) for i in range(num_producers)]
    consumers = [threading.Thread(target=consumer) for _ in range(num_consumers)]
    
    for t in producers + consumers:
        t.start()
    for t in producers:
        t.join()
    
    buf.close()
    
    for t in consumers:
        t.join(timeout=5)
    
    return buf.produced_count, len(results)
