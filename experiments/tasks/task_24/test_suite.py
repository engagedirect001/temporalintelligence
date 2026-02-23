import pytest
from buggy_code import SkipList


def test_insert_and_search():
    sl = SkipList(random_seed=42)
    sl.insert(3, "three")
    sl.insert(1, "one")
    sl.insert(5, "five")
    
    assert sl.search(1) == "one"
    assert sl.search(3) == "three"
    assert sl.search(5) == "five"
    assert sl.search(2) is None


def test_update_existing():
    sl = SkipList(random_seed=42)
    sl.insert(1, "old")
    sl.insert(1, "new")
    assert sl.search(1) == "new"
    assert sl.size == 1


def test_delete_basic():
    sl = SkipList(random_seed=42)
    sl.insert(1, "a")
    sl.insert(2, "b")
    sl.insert(3, "c")
    
    assert sl.delete(2) is True
    assert sl.search(2) is None
    assert sl.search(1) == "a"
    assert sl.search(3) == "c"


def test_delete_preserves_structure():
    """Bug 1: delete corrupts forward pointers at higher levels."""
    sl = SkipList(random_seed=1)  # seed for reproducible levels
    
    # Insert enough items to create multi-level structure
    for i in range(20):
        sl.insert(i, f"val_{i}")
    
    # Delete some items in the middle
    sl.delete(5)
    sl.delete(10)
    sl.delete(15)
    
    # Verify all remaining items are still accessible
    for i in range(20):
        if i in (5, 10, 15):
            assert sl.search(i) is None, f"Deleted key {i} still found"
        else:
            assert sl.search(i) == f"val_{i}", f"Key {i} lost after deletions"
    
    # Verify sorted order is maintained
    items = sl.to_list()
    keys = [k for k, v in items]
    assert keys == sorted(keys), f"Order broken: {keys}"
    assert len(items) == 17


def test_range_query_inclusive():
    """Bug 3: range_query end_key should be inclusive."""
    sl = SkipList(random_seed=42)
    for i in [1, 3, 5, 7, 9]:
        sl.insert(i, i * 10)
    
    result = sl.range_query(3, 7)
    keys = [k for k, v in result]
    assert 7 in keys, f"End key 7 should be included, got keys {keys}"
    assert keys == [3, 5, 7]


def test_range_query_empty():
    sl = SkipList(random_seed=42)
    sl.insert(1, "a")
    sl.insert(10, "b")
    result = sl.range_query(3, 5)
    assert result == []


def test_delete_nonexistent():
    sl = SkipList(random_seed=42)
    sl.insert(1, "a")
    assert sl.delete(99) is False
    assert sl.size == 1


def test_many_operations():
    sl = SkipList(random_seed=42)
    for i in range(100):
        sl.insert(i, i)
    
    for i in range(0, 100, 2):
        sl.delete(i)
    
    assert sl.size == 50
    for i in range(100):
        if i % 2 == 0:
            assert sl.search(i) is None
        else:
            assert sl.search(i) == i
