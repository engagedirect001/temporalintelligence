"""
Task 15: Concurrent Priority Task Queue (Concurrency + Data Structure)
Category: Combined — concurrency + heap bugs
"""
import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class PriorityItem:
    priority: int
    sequence: int  # tie-breaker for FIFO within same priority
    item: Any = field(compare=False)


class ConcurrentPriorityQueue:
    """Thread-safe priority queue with task cancellation."""
    
    def __init__(self):
        self.heap = []
        self.lock = threading.Lock()
        self.not_empty = threading.Condition(self.lock)
        self.sequence = 0
        self.cancelled = set()  # set of cancelled sequence numbers
    
    def _sift_up(self, idx):
        while idx > 0:
            parent = (idx - 1) // 2
            if self.heap[idx] < self.heap[parent]:
                self.heap[idx], self.heap[parent] = self.heap[parent], self.heap[idx]
                idx = parent
            else:
                break
    
    def _sift_down(self, idx):
        n = len(self.heap)
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2
            
            if left < n and self.heap[left] < self.heap[smallest]:
                smallest = left
            if right < n and self.heap[right] < self.heap[smallest]:
                smallest = right
            
            if smallest != idx:
                self.heap[idx], self.heap[smallest] = self.heap[smallest], self.heap[idx]
                idx = smallest
            else:
                break
    
    def put(self, item, priority=0):
        """Add item. Lower priority number = higher priority."""
        with self.not_empty:
            entry = PriorityItem(priority, self.sequence, item)
            self.sequence += 1
            self.heap.append(entry)
            self._sift_up(len(self.heap) - 1)
            self.not_empty.notify()
            return entry.sequence  # return handle for cancellation
    
    def get(self, timeout=None):
        """Remove and return highest priority item."""
        with self.not_empty:
            while True:
                while not self.heap:
                    # Bug 1: doesn't handle timeout correctly — if we wait
                    # and get notified but item is cancelled, we might wait forever
                    if not self.not_empty.wait(timeout=timeout):
                        raise TimeoutError("Queue get timed out")
                
                # Pop min
                if len(self.heap) == 1:
                    entry = self.heap.pop()
                else:
                    entry = self.heap[0]
                    self.heap[0] = self.heap.pop()
                    self._sift_down(0)
                
                # Bug 2: checks cancelled AFTER removing from heap
                # but doesn't re-calculate timeout for the time already waited
                if entry.sequence in self.cancelled:
                    self.cancelled.discard(entry.sequence)
                    continue  # skip cancelled, but timeout is now wrong
                
                return entry.item
    
    def cancel(self, sequence_id):
        """Cancel a pending item by sequence ID."""
        with self.lock:
            # Bug 3: only adds to cancelled set, doesn't notify waiting threads
            # So if a thread is waiting on empty queue and cancel makes
            # the effective queue empty, it's fine — but if we cancel
            # the only item, the waiting thread will pop it and loop
            # without resetting its timeout
            self.cancelled.add(sequence_id)
    
    def size(self):
        with self.lock:
            return len(self.heap) - len(self.cancelled & {e.sequence for e in self.heap})
    
    def __len__(self):
        return self.size()
