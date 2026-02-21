"""
Task 17: B-Tree Insert and Search
Category: Combined — data structure + algorithm bugs
"""


class BTreeNode:
    def __init__(self, leaf=True):
        self.keys = []
        self.children = []
        self.leaf = leaf


class BTree:
    """B-Tree of minimum degree t."""
    
    def __init__(self, t=2):
        self.t = t
        self.root = BTreeNode(leaf=True)
    
    def search(self, key, node=None):
        """Search for key. Returns (node, index) or None."""
        if node is None:
            node = self.root
        
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        
        if i < len(node.keys) and key == node.keys[i]:
            return (node, i)
        
        # Bug 1: searches child even when node is a leaf (should return None)
        if i < len(node.children):
            return self.search(key, node.children[i])
        
        return None
    
    def insert(self, key):
        root = self.root
        
        if len(root.keys) == 2 * self.t - 1:
            new_root = BTreeNode(leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root
        
        self._insert_non_full(self.root, key)
    
    def _insert_non_full(self, node, key):
        i = len(node.keys) - 1
        
        if node.leaf:
            # Insert key in sorted position
            node.keys.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                i -= 1
            node.keys[i + 1] = key
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            
            if len(node.children[i].keys) == 2 * self.t - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            
            self._insert_non_full(node.children[i], key)
    
    def _split_child(self, parent, idx):
        t = self.t
        child = parent.children[idx]
        new_node = BTreeNode(leaf=child.leaf)
        
        # Bug 2: median key index should be t-1, takes wrong slice
        median_key = child.keys[t]  # Bug: should be child.keys[t-1]
        
        # Bug 3: slicing is off — new_node gets wrong keys
        new_node.keys = child.keys[t+1:]  # Should be child.keys[t:]
        child.keys = child.keys[:t]       # Should be child.keys[:t-1]
        
        if not child.leaf:
            new_node.children = child.children[t+1:]
            child.children = child.children[:t+1]
        
        parent.children.insert(idx + 1, new_node)
        parent.keys.insert(idx, median_key)
    
    def inorder(self, node=None):
        """Return all keys in sorted order."""
        if node is None:
            node = self.root
        
        result = []
        for i, key in enumerate(node.keys):
            if not node.leaf and i < len(node.children):
                result.extend(self.inorder(node.children[i]))
            result.append(key)
        
        if not node.leaf and len(node.children) > len(node.keys):
            result.extend(self.inorder(node.children[-1]))
        
        return result
