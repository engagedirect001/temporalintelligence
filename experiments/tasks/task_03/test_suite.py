import pytest
from buggy_code import MinHeap


def test_basic_push_pop():
    h = MinHeap()
    h.push(3, "c")
    h.push(1, "a")
    h.push(2, "b")
    assert h.pop() == (1, "a")
    assert h.pop() == (2, "b")
    assert h.pop() == (3, "c")


def test_decrease_key_basic():
    h = MinHeap()
    h.push(5, "a")
    h.push(3, "b")
    h.push(7, "c")
    h.decrease_key("c", 1)
    assert h.peek() == (1, "c")


def test_swap_preserves_index_map():
    """Bug 1: _swap updates index_map backwards."""
    h = MinHeap()
    h.push(5, "x")
    h.push(3, "y")
    h.push(1, "z")
    # After push(1, "z"), sift_up should swap. Check index_map consistency.
    for priority, key in h.heap:
        assert h.index_map[key] == h.heap.index((priority, key)), \
            f"index_map[{key}]={h.index_map[key]} but actual index={h.heap.index((priority, key))}"


def test_sift_down_picks_correct_child():
    """Bug 2: sift_down compares right child with idx instead of smallest."""
    h = MinHeap()
    for p, k in [(1, "a"), (3, "b"), (2, "c"), (5, "d"), (4, "e")]:
        h.push(p, k)
    
    h.pop()  # remove (1, "a")
    # Heap should now have min = 2
    assert h.peek()[0] == 2, f"Expected min priority 2, got {h.peek()[0]}"
    
    results = []
    while h:
        results.append(h.pop()[0])
    assert results == sorted(results), f"Not in sorted order: {results}"


def test_decrease_key_rejects_increase():
    """Bug 3: decrease_key should reject new_priority >= old_priority."""
    h = MinHeap()
    h.push(2, "a")
    h.push(5, "b")
    
    with pytest.raises(ValueError):
        h.decrease_key("a", 10)  # should raise, not silently corrupt heap


def test_many_operations_sorted_output():
    """Combined test: push many, decrease some, pop all in order."""
    h = MinHeap()
    items = [(10, "j"), (4, "d"), (7, "g"), (1, "a"), (8, "h"),
             (3, "c"), (6, "f"), (9, "i"), (2, "b"), (5, "e")]
    for p, k in items:
        h.push(p, k)
    
    h.decrease_key("j", 0)  # 10 -> 0
    
    results = []
    while h:
        results.append(h.pop()[0])
    assert results == sorted(results), f"Not sorted: {results}"


def test_pop_empty():
    h = MinHeap()
    with pytest.raises(IndexError):
        h.pop()


def test_decrease_key_missing():
    h = MinHeap()
    with pytest.raises(KeyError):
        h.decrease_key("missing", 1)
