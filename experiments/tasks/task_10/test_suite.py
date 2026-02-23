import pytest
from buggy_code import RobinHoodHashTable


def test_basic_put_get():
    ht = RobinHoodHashTable()
    ht.put("a", 1)
    assert ht.get("a") == 1


def test_update_existing():
    ht = RobinHoodHashTable()
    ht.put("a", 1)
    ht.put("a", 2)
    assert ht.get("a") == 2
    assert len(ht) == 1


def test_delete_and_get():
    ht = RobinHoodHashTable()
    ht.put("a", 1)
    ht.put("b", 2)
    ht.delete("a")
    assert ht.get("a") is None
    assert ht.get("b") == 2


def test_delete_and_resize():
    """Bug 3: DELETED entries get re-inserted during resize."""
    ht = RobinHoodHashTable(capacity=4)
    ht.put("a", 1)
    ht.put("b", 2)
    ht.delete("a")
    
    # Force resize by adding more items
    ht.put("c", 3)
    ht.put("d", 4)
    ht.put("e", 5)
    
    assert ht.get("a") is None, "Deleted key 'a' reappeared after resize"
    assert "a" not in ht


def test_robin_hood_property():
    """After many insertions, verify all elements are retrievable."""
    ht = RobinHoodHashTable(capacity=8)
    items = {f"key_{i}": i for i in range(20)}
    for k, v in items.items():
        ht.put(k, v)
    
    for k, v in items.items():
        assert ht.get(k) == v, f"Lost {k}={v}"


def test_get_early_termination():
    """Bug 2: get() should terminate based on probe distance, not capacity."""
    ht = RobinHoodHashTable(capacity=16)
    # Insert a few items that hash to same bucket
    for i in range(5):
        ht.put(f"k{i}", i)
    
    # Looking up a missing key shouldn't scan entire table
    result = ht.get("nonexistent")
    assert result is None


def test_collision_handling():
    """Test that collisions are handled correctly with displacement."""
    ht = RobinHoodHashTable(capacity=8)
    # These might collide depending on hash
    keys = ["cat", "dog", "rat", "bat", "hat"]
    for i, k in enumerate(keys):
        ht.put(k, i)
    
    for i, k in enumerate(keys):
        assert ht.get(k) == i, f"Wrong value for {k}"


def test_contains():
    ht = RobinHoodHashTable()
    ht.put("x", 42)
    assert "x" in ht
    assert "y" not in ht


def test_delete_missing_raises():
    ht = RobinHoodHashTable()
    with pytest.raises(KeyError):
        ht.delete("missing")
