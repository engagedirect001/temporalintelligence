"""
Task 03: Min-Heap with Decrease-Key Operation
Category: Data structure bugs
"""

class MinHeap:
    def __init__(self):
        self.heap = []
        self.index_map = {}  # key -> index in heap
    
    def _swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        # Bug 1: index_map update is backwards after swap
        self.index_map[self.heap[i][1]] = j  # should be i
        self.index_map[self.heap[j][1]] = i  # should be j
    
    def _sift_up(self, idx):
        while idx > 0:
            parent = (idx - 1) // 2
            if self.heap[idx][0] < self.heap[parent][0]:
                self._swap(idx, parent)
                idx = parent
            else:
                break
    
    def _sift_down(self, idx):
        n = len(self.heap)
        while True:
            smallest = idx
            left = 2 * idx + 1
            right = 2 * idx + 2
            
            if left < n and self.heap[left][0] < self.heap[smallest][0]:
                smallest = left
            # Bug 2: compares right with idx instead of current smallest
            if right < n and self.heap[right][0] < self.heap[idx][0]:
                smallest = right
            
            if smallest != idx:
                self._swap(idx, smallest)
                idx = smallest
            else:
                break
    
    def push(self, priority, key):
        self.heap.append((priority, key))
        self.index_map[key] = len(self.heap) - 1
        self._sift_up(len(self.heap) - 1)
    
    def pop(self):
        if not self.heap:
            raise IndexError("pop from empty heap")
        
        min_item = self.heap[0]
        last = self.heap.pop()
        
        if self.heap:
            self.heap[0] = last
            self.index_map[last[1]] = 0
        
        del self.index_map[min_item[1]]
        
        if self.heap:
            self._sift_down(0)
        
        return min_item
    
    def decrease_key(self, key, new_priority):
        if key not in self.index_map:
            raise KeyError(f"Key {key} not found")
        
        idx = self.index_map[key]
        old_priority = self.heap[idx][0]
        
        # Bug 3: doesn't validate that new_priority < old_priority
        # and silently allows increase (breaking heap invariant)
        self.heap[idx] = (new_priority, key)
        self._sift_up(idx)
    
    def peek(self):
        if not self.heap:
            raise IndexError("peek at empty heap")
        return self.heap[0]
    
    def __len__(self):
        return len(self.heap)
    
    def __bool__(self):
        return len(self.heap) > 0
