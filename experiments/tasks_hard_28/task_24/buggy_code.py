"""
Task 24: Skip List Implementation
Category: Hardest — data structure + probabilistic + subtle pointer bugs
"""
import random


class SkipNode:
    def __init__(self, key, value, level):
        self.key = key
        self.value = value
        self.forward = [None] * (level + 1)
    
    def __repr__(self):
        return f"SkipNode({self.key})"


class SkipList:
    MAX_LEVEL = 16
    P = 0.5
    
    def __init__(self, random_seed=None):
        self.header = SkipNode(float('-inf'), None, self.MAX_LEVEL)
        self.level = 0
        self.size = 0
        self._rng = random.Random(random_seed)
    
    def _random_level(self):
        lvl = 0
        while self._rng.random() < self.P and lvl < self.MAX_LEVEL:
            lvl += 1
        return lvl
    
    def search(self, key):
        current = self.header
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
        
        current = current.forward[0]
        if current and current.key == key:
            return current.value
        return None
    
    def insert(self, key, value):
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        
        current = current.forward[0]
        
        if current and current.key == key:
            current.value = value
            return
        
        new_level = self._random_level()
        
        if new_level > self.level:
            for i in range(self.level + 1, new_level + 1):
                update[i] = self.header
            self.level = new_level
        
        new_node = SkipNode(key, value, new_level)
        
        for i in range(new_level + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node
        
        self.size += 1
    
    def delete(self, key):
        update = [None] * (self.MAX_LEVEL + 1)
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < key:
                current = current.forward[i]
            update[i] = current
        
        target = current.forward[0]
        
        if not target or target.key != key:
            return False
        
        for i in range(self.level + 1):
            # Bug 1: doesn't check if update[i].forward[i] is the target node
            # This corrupts forward pointers when update[i] points past target at level i
            if update[i] is None:
                break
            update[i].forward[i] = target.forward[i]
        
        # Bug 2: level adjustment goes wrong — should check header.forward,
        # but checks self.level without verifying
        while self.level > 0 and self.header.forward[self.level] is None:
            self.level -= 1
        
        self.size -= 1
        return True
    
    def range_query(self, start_key, end_key):
        """Return all (key, value) pairs where start_key <= key <= end_key."""
        result = []
        current = self.header
        
        for i in range(self.level, -1, -1):
            while current.forward[i] and current.forward[i].key < start_key:
                current = current.forward[i]
        
        current = current.forward[0]
        
        # Bug 3: uses < instead of <= for end_key comparison
        while current and current.key < end_key:
            result.append((current.key, current.value))
            current = current.forward[0]
        
        return result
    
    def to_list(self):
        result = []
        current = self.header.forward[0]
        while current:
            result.append((current.key, current.value))
            current = current.forward[0]
        return result
