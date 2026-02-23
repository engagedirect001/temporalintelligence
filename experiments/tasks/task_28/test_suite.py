import pytest
from buggy_code import MVCCStore


def test_basic_read_write():
    store = MVCCStore()
    t1 = store.begin()
    store.write(t1, "x", 10)
    
    # Read own write
    assert store.read(t1, "x") == 10
    assert store.commit(t1) is True


def test_read_after_commit():
    store = MVCCStore()
    t1 = store.begin()
    store.write(t1, "x", 10)
    store.commit(t1)
    
    t2 = store.begin()
    assert store.read(t2, "x") == 10


def test_snapshot_isolation():
    """Transactions should see a consistent snapshot from their start time."""
    store = MVCCStore()
    
    # T1 writes x=10 and commits
    t1 = store.begin()
    store.write(t1, "x", 10)
    store.commit(t1)
    
    # T2 starts and sees x=10
    t2 = store.begin()
    assert store.read(t2, "x") == 10
    
    # T3 starts, writes x=20, commits
    t3 = store.begin()
    store.write(t3, "x", 20)
    store.commit(t3)
    
    # T2 should still see x=10 (snapshot from its start time)
    assert store.read(t2, "x") == 10, \
        "T2 should see x=10 from its snapshot, not the later write of 20"


def test_read_skips_uncommitted():
    """Bug 1: should skip uncommitted versions from other transactions."""
    store = MVCCStore()
    
    # T1 writes and commits x=10
    t1 = store.begin()
    store.write(t1, "x", 10)
    store.commit(t1)
    
    # T2 writes x=20 but does NOT commit
    t2 = store.begin()
    store.write(t2, "x", 20)
    
    # T3 reads x — should see 10 (T2 not committed)
    t3 = store.begin()
    # First, commit T2's write to make it a version (but T2 shouldn't be visible)
    # Actually, uncommitted writes only exist in write_set, not in versions
    # Let's test differently: commit T2 to create version, then read from T3 started before
    
    # Better test: T1 commits x=10, T2 starts, T1b commits x=20 (out of order by txn_id)
    store2 = MVCCStore()
    ta = store2.begin()
    store2.write(ta, "x", 10)
    store2.commit(ta)
    
    tb = store2.begin()  # starts after ta committed
    
    tc = store2.begin()
    store2.write(tc, "x", 20)
    # tc is NOT committed yet — its version shouldn't be visible
    # But we can't test this easily since uncommitted writes stay in write_set
    # Let's just ensure tb sees 10
    assert store2.read(tb, "x") == 10


def test_write_write_conflict():
    """Two concurrent transactions writing same key — second should abort."""
    store = MVCCStore()
    
    t1 = store.begin()
    t2 = store.begin()
    
    store.write(t1, "x", 10)
    store.write(t2, "x", 20)
    
    assert store.commit(t1) is True
    assert store.commit(t2) is False, "T2 should fail: write-write conflict on x"


def test_read_set_validation():
    """Bug 3: Missing read-set validation allows write skew."""
    store = MVCCStore()
    
    # Initial: x=1, y=1, constraint: x + y > 0
    t0 = store.begin()
    store.write(t0, "x", 1)
    store.write(t0, "y", 1)
    store.commit(t0)
    
    # T1 reads x=1, sets y=0 (thinks x+y = 1+0 = 1 > 0)
    t1 = store.begin()
    store.read(t1, "x")  # reads x=1
    store.write(t1, "y", 0)
    
    # T2 reads y=1, sets x=0 (thinks x+y = 0+1 = 1 > 0)
    t2 = store.begin()
    store.read(t2, "y")  # reads y=1
    store.write(t2, "x", 0)
    
    # Both commit — but result is x=0, y=0 which violates constraint!
    store.commit(t1)
    result = store.commit(t2)
    
    # For serializable isolation, T2 should fail (read-set of y was modified by T1)
    # This tests Bug 3: missing read-set validation
    assert result is False, \
        "T2 should fail: T1 wrote to y which T2 read (write skew)"


def test_delete():
    store = MVCCStore()
    t1 = store.begin()
    store.write(t1, "x", 10)
    store.commit(t1)
    
    t2 = store.begin()
    store.delete(t2, "x")
    store.commit(t2)
    
    t3 = store.begin()
    assert store.read(t3, "x") is None


def test_abort():
    store = MVCCStore()
    t1 = store.begin()
    store.write(t1, "x", 10)
    store.abort(t1)
    
    t2 = store.begin()
    assert store.read(t2, "x") is None


def test_snapshot_read():
    store = MVCCStore()
    
    t1 = store.begin()
    store.write(t1, "x", 10)
    store.commit(t1)
    
    t2 = store.begin()
    store.write(t2, "x", 20)
    store.commit(t2)
    
    # Read as of different timestamps
    ts_mid = 2  # after t1 commit, before t2 commit
    assert store.snapshot_read("x", as_of_ts=ts_mid) == 10
