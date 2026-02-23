import pytest
from buggy_code import BTree


def test_insert_and_search():
    bt = BTree(t=2)
    for k in [10, 20, 5, 6]:
        bt.insert(k)
    
    assert bt.search(10) is not None
    assert bt.search(20) is not None
    assert bt.search(5) is not None


def test_search_missing():
    """Bug 1: searching for missing key in leaf should return None, not error."""
    bt = BTree(t=2)
    for k in [10, 20, 30]:
        bt.insert(k)
    
    result = bt.search(15)
    assert result is None, "Missing key should return None"


def test_inorder_traversal():
    bt = BTree(t=2)
    keys = [3, 7, 1, 5, 9, 2, 8, 4, 6]
    for k in keys:
        bt.insert(k)
    
    result = bt.inorder()
    assert result == sorted(keys), f"Expected {sorted(keys)}, got {result}"


def test_split_correctness():
    """Bug 2+3: split uses wrong median and wrong slicing."""
    bt = BTree(t=2)
    # With t=2, max keys per node = 3, split at 4th insert
    for k in [10, 20, 30, 40]:
        bt.insert(k)
    
    result = bt.inorder()
    assert result == [10, 20, 30, 40], f"Expected [10,20,30,40], got {result}"
    
    # All keys should be searchable
    for k in [10, 20, 30, 40]:
        assert bt.search(k) is not None, f"Key {k} not found after split"


def test_many_inserts():
    bt = BTree(t=3)
    keys = list(range(1, 51))
    for k in keys:
        bt.insert(k)
    
    result = bt.inorder()
    assert result == keys, f"Inorder doesn't match: got {result[:10]}..."
    
    for k in keys:
        assert bt.search(k) is not None, f"Key {k} not found"


def test_reverse_inserts():
    bt = BTree(t=2)
    keys = list(range(20, 0, -1))
    for k in keys:
        bt.insert(k)
    
    result = bt.inorder()
    assert result == sorted(keys), f"Expected sorted keys, got {result}"


def test_search_not_found_deep_tree():
    bt = BTree(t=2)
    for k in range(1, 30):
        bt.insert(k)
    
    assert bt.search(100) is None
    assert bt.search(0) is None
    assert bt.search(-5) is None
