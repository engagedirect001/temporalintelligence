import pytest
import asyncio
from buggy_code import ConnectionPool, Connection


class MockTime:
    def __init__(self, start=0.0):
        self._now = start
    def __call__(self):
        return self._now
    def advance(self, s):
        self._now += s


@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def test_basic_acquire_release(event_loop):
    async def run():
        clock = MockTime()
        pool = ConnectionPool(max_per_host=5, max_total=20, time_fn=clock)
        conn = await pool.acquire("example.com")
        assert conn.host == "example.com"
        assert conn.is_busy is True
        await pool.release(conn)
        assert conn.is_busy is False
    event_loop.run_until_complete(run())


def test_per_host_limit(event_loop):
    """Bug 1: per-host limit check uses total_count instead of host pool size."""
    async def run():
        clock = MockTime()
        pool = ConnectionPool(max_per_host=2, max_total=10, time_fn=clock)
        
        # Acquire 2 for host A
        c1 = await pool.acquire("hostA")
        c2 = await pool.acquire("hostA")
        
        # Should be at per-host limit for hostA
        # But should still allow hostB
        c3 = await asyncio.wait_for(pool.acquire("hostB"), timeout=1.0)
        assert c3 is not None, "Should allow connections to different host"
        assert c3.host == "hostB"
    
    event_loop.run_until_complete(run())


def test_reuse_idle_connection(event_loop):
    async def run():
        clock = MockTime()
        pool = ConnectionPool(max_per_host=5, max_total=20, time_fn=clock)
        
        conn1 = await pool.acquire("example.com")
        await pool.release(conn1)
        
        conn2 = await pool.acquire("example.com")
        assert conn2 is conn1, "Should reuse idle connection"
    
    event_loop.run_until_complete(run())


def test_exhausted_connection_removed(event_loop):
    """Bug 3: total_count not decremented when exhausted connection is removed."""
    async def run():
        clock = MockTime()
        pool = ConnectionPool(max_per_host=5, max_total=2, time_fn=clock)
        
        conn = await pool.acquire("example.com")
        conn.request_count = conn.max_requests  # force exhaustion
        await pool.release(conn)
        
        # Should be able to create new connections since exhausted one was removed
        assert pool.total_count == 1, \
            f"total_count should be 0 after exhausted removal, got {pool.total_count}"
    
    event_loop.run_until_complete(run())


def test_close_idle(event_loop):
    async def run():
        clock = MockTime()
        pool = ConnectionPool(max_per_host=5, max_total=20, max_idle_time=30.0,
                              time_fn=clock)
        
        conn = await pool.acquire("example.com")
        await pool.release(conn)
        
        clock.advance(31)
        await pool.close_idle()
        
        assert pool.total_count == 0
        assert len(pool.pools["example.com"]) == 0
    
    event_loop.run_until_complete(run())


def test_stats_tracking(event_loop):
    async def run():
        clock = MockTime()
        pool = ConnectionPool(max_per_host=5, max_total=20, time_fn=clock)
        
        conn = await pool.acquire("example.com")
        await pool.release(conn)
        
        stats = pool.get_stats()
        assert stats["created"] == 1
        assert stats["acquired"] == 1
        assert stats["released"] == 1
    
    event_loop.run_until_complete(run())
