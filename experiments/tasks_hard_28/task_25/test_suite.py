import pytest
from buggy_code import EventStore, Event, Projection


def test_basic_set_and_rebuild():
    store = EventStore()
    store.append(Event("set", {"key": "x", "value": 1}, version=0))
    store.append(Event("set", {"key": "y", "value": 2}, version=1))
    
    state = store.rebuild_state()
    assert state == {"x": 1, "y": 2}


def test_increment():
    store = EventStore()
    store.append(Event("set", {"key": "counter", "value": 0}, version=0))
    store.append(Event("increment", {"key": "counter", "amount": 5}, version=1))
    store.append(Event("increment", {"key": "counter", "amount": 3}, version=2))
    
    state = store.rebuild_state()
    assert state["counter"] == 8


def test_delete_missing_key():
    """Bug 3: deleting non-existent key should not raise."""
    store = EventStore()
    store.append(Event("set", {"key": "x", "value": 1}, version=0))
    store.append(Event("delete", {"key": "missing"}, version=1))
    
    state = store.rebuild_state()  # should not raise
    assert state == {"x": 1}


def test_snapshot_isolation():
    """Bug 2: snapshot should be deep-copied to prevent mutation."""
    store = EventStore()
    store.snapshot_interval = 2
    
    store.append(Event("set", {"key": "a", "value": 1}, version=0))
    store.append(Event("set", {"key": "b", "value": 2}, version=1))
    # Snapshot taken at version 1
    
    store.append(Event("set", {"key": "c", "value": 3}, version=2))
    
    # First rebuild (up to version 2)
    state1 = store.rebuild_state()
    assert state1 == {"a": 1, "b": 2, "c": 3}
    
    # Rebuild again up to snapshot version (1)
    state2 = store.rebuild_state(1)
    assert state2 == {"a": 1, "b": 2}, \
        f"Snapshot corrupted: expected {{'a':1,'b':2}}, got {state2}"


def test_version_ordering():
    """Bug 1: should reject or handle out-of-order versions."""
    store = EventStore()
    store.append(Event("set", {"key": "x", "value": 1}, version=0))
    store.append(Event("set", {"key": "y", "value": 2}, version=5))  # gap
    store.append(Event("set", {"key": "z", "value": 3}, version=2))  # out of order
    
    # Events should be in version order for correct rebuild
    events = store.events
    versions = [e.version for e in events]
    assert versions == sorted(versions), \
        f"Events should be in version order, got {versions}"


def test_rebuild_partial():
    store = EventStore()
    for i in range(5):
        store.append(Event("set", {"key": f"k{i}", "value": i}, version=i))
    
    state = store.rebuild_state(2)
    assert state == {"k0": 0, "k1": 1, "k2": 2}


def test_projection():
    store = EventStore()
    proj = Projection(store)
    
    store.append(Event("set", {"key": "x", "value": 10}, version=0))
    assert proj.query("x") == 10
    
    store.append(Event("increment", {"key": "x", "amount": 5}, version=1))
    assert proj.query("x") == 15


def test_compact():
    store = EventStore()
    for i in range(20):
        store.append(Event("set", {"key": f"k{i}", "value": i}, version=i))
    
    store.compact(keep_after_version=15)
    
    state = store.rebuild_state()
    # Should still have all keys
    for i in range(20):
        assert state.get(f"k{i}") == i, f"Lost k{i} after compaction"
