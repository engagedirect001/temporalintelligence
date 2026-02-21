import pytest
from buggy_code import SPSCRingBuffer, run_spsc_test


def test_basic_put_get():
    buf = SPSCRingBuffer(8)  # power of 2
    assert buf.put(1) is True
    assert buf.put(2) is True
    assert buf.get() == 1
    assert buf.get() == 2


def test_empty():
    buf = SPSCRingBuffer(8)
    assert buf.is_empty() is True
    assert buf.get() is None


def test_full():
    buf = SPSCRingBuffer(4)
    buf.put("a")
    buf.put("b")
    buf.put("c")
    assert buf.is_full() is True
    assert buf.put("d") is False


def test_non_power_of_two_capacity():
    """Bug 1+2: non-power-of-2 capacity breaks mask-based arithmetic."""
    buf = SPSCRingBuffer(10)  # NOT power of 2
    
    # Fill and drain multiple times to test wraparound
    for cycle in range(3):
        for i in range(9):  # capacity - 1
            success = buf.put(f"c{cycle}_i{i}")
            assert success, f"Put failed at cycle {cycle}, item {i}"
        
        items = buf.drain()
        assert len(items) == 9, \
            f"Cycle {cycle}: expected 9 items, got {len(items)}"


def test_wraparound_correctness():
    """Test that items survive wrap-around."""
    buf = SPSCRingBuffer(4)
    
    # Fill to capacity-1
    buf.put(1)
    buf.put(2)
    buf.put(3)
    
    # Drain
    assert buf.get() == 1
    assert buf.get() == 2
    assert buf.get() == 3
    
    # Fill again (head has wrapped)
    buf.put(4)
    buf.put(5)
    buf.put(6)
    
    assert buf.get() == 4
    assert buf.get() == 5
    assert buf.get() == 6


def test_size_calculation():
    """Bug 2: _size is wrong for non-power-of-2."""
    buf = SPSCRingBuffer(6)  # not power of 2
    
    buf.put("a")
    buf.put("b")
    buf.put("c")
    
    # Size should be 3
    assert buf._size() == 3, f"Expected size 3, got {buf._size()}"
    
    buf.get()
    assert buf._size() == 2, f"Expected size 2, got {buf._size()}"


def test_spsc_concurrent():
    """Integration test: concurrent producer/consumer."""
    writes, reads, items = run_spsc_test(100, 16)
    assert writes == 100
    assert reads == 100
    assert items == list(range(100)), "Items should be in order for SPSC"


def test_spsc_concurrent_non_power_of_2():
    """Bug 1+2: concurrent with non-power-of-2 buffer."""
    writes, reads, items = run_spsc_test(50, 10)
    assert writes == 50
    assert reads == 50
    assert len(items) == 50


def test_overflow_tracking():
    buf = SPSCRingBuffer(4)
    buf.put(1)
    buf.put(2)
    buf.put(3)
    assert buf.put(4) is False
    assert buf.overflow_count == 1
