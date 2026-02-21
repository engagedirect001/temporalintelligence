"""
Task 10: Open-Addressing Hash Table with Robin Hood Hashing
Category: Data structure bugs
"""


class RobinHoodHashTable:
    """Hash table using Robin Hood hashing (open addressing with displacement)."""
    
    EMPTY = object()
    DELETED = object()
    
    def __init__(self, capacity=8):
        self.capacity = capacity
        self.size = 0
        self.keys = [self.EMPTY] * capacity
        self.values = [None] * capacity
    
    def _hash(self, key):
        return hash(key) % self.capacity
    
    def _probe_distance(self, idx, key):
        """How far this key is from its ideal position."""
        ideal = self._hash(key)
        # Bug 1: doesn't handle wrap-around correctly
        return idx - ideal if idx >= ideal else idx + self.capacity - ideal
    
    def put(self, key, value):
        if self.size >= self.capacity * 0.7:
            self._resize()
        
        idx = self._hash(key)
        dist = 0
        insert_key = key
        insert_val = value
        
        while True:
            if self.keys[idx] is self.EMPTY or self.keys[idx] is self.DELETED:
                self.keys[idx] = insert_key
                self.values[idx] = insert_val
                self.size += 1
                return
            
            if self.keys[idx] == key:
                # Update existing
                self.values[idx] = value
                return
            
            # Robin Hood: steal from the rich (swap if current element is closer to home)
            existing_dist = self._probe_distance(idx, self.keys[idx])
            if dist > existing_dist:
                # Swap
                self.keys[idx], insert_key = insert_key, self.keys[idx]
                self.values[idx], insert_val = insert_val, self.values[idx]
                dist = existing_dist
            
            dist += 1
            idx = (idx + 1) % self.capacity
    
    def get(self, key, default=None):
        idx = self._hash(key)
        dist = 0
        
        while True:
            if self.keys[idx] is self.EMPTY:
                return default
            
            if self.keys[idx] == key:
                return self.values[idx]
            
            # Bug 2: Robin Hood property means we can stop early,
            # but this check is wrong — should compare with existing element's distance
            if dist > self.capacity:
                return default
            
            dist += 1
            idx = (idx + 1) % self.capacity
    
    def delete(self, key):
        idx = self._hash(key)
        dist = 0
        
        while True:
            if self.keys[idx] is self.EMPTY:
                raise KeyError(key)
            
            if self.keys[idx] == key:
                # Bug 3: Uses DELETED tombstone but _resize doesn't skip DELETED
                # entries during rehash — they get inserted as real entries
                self.keys[idx] = self.DELETED
                self.values[idx] = None
                self.size -= 1
                return
            
            dist += 1
            idx = (idx + 1) % self.capacity
    
    def _resize(self):
        old_keys = self.keys
        old_values = self.values
        self.capacity *= 2
        self.keys = [self.EMPTY] * self.capacity
        self.values = [None] * self.capacity
        self.size = 0
        
        for k, v in zip(old_keys, old_values):
            # Bug 3 manifests: doesn't check for DELETED
            if k is not self.EMPTY:
                self.put(k, v)
    
    def __contains__(self, key):
        return self.get(key, self.EMPTY) is not self.EMPTY
    
    def __len__(self):
        return self.size
