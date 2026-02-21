"""
Task 16: Async HTTP Client with Connection Pooling
Category: Combined — concurrency + API/protocol bugs
"""
import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


@dataclass
class Connection:
    host: str
    port: int
    is_busy: bool = False
    request_count: int = 0
    max_requests: int = 100
    created_at: float = 0.0
    
    @property
    def is_exhausted(self):
        return self.request_count >= self.max_requests


class ConnectionPool:
    """Async connection pool with per-host limits."""
    
    def __init__(self, max_per_host=5, max_total=20, max_idle_time=30.0,
                 time_fn=None):
        self.max_per_host = max_per_host
        self.max_total = max_total
        self.max_idle_time = max_idle_time
        self.time_fn = time_fn or asyncio.get_event_loop().time
        
        self.pools = defaultdict(list)  # host -> [Connection]
        self.total_count = 0
        self._lock = asyncio.Lock()
        self._host_events = defaultdict(asyncio.Event)
        self.stats = {"acquired": 0, "released": 0, "created": 0, "closed": 0}
    
    async def acquire(self, host, port=443):
        """Get a connection from the pool or create one."""
        async with self._lock:
            # Try to find an idle connection
            pool = self.pools[host]
            for conn in pool:
                if not conn.is_busy and not conn.is_exhausted:
                    conn.is_busy = True
                    conn.request_count += 1
                    self.stats["acquired"] += 1
                    return conn
            
            # Create new if under limits
            # Bug 1: checks per-host limit against total count instead of host count
            if self.total_count < self.max_per_host and self.total_count < self.max_total:
                conn = Connection(
                    host=host, port=port,
                    is_busy=True, request_count=1,
                    created_at=self.time_fn()
                )
                pool.append(conn)
                self.total_count += 1
                self.stats["created"] += 1
                self.stats["acquired"] += 1
                return conn
        
        # Bug 2: waits outside the lock, but when woken up, doesn't re-check
        # under lock — another coroutine might grab the connection first
        await self._host_events[host].wait()
        self._host_events[host].clear()
        return await self.acquire(host, port)  # recursive retry, could stack overflow
    
    async def release(self, conn):
        """Return connection to pool."""
        async with self._lock:
            conn.is_busy = False
            self.stats["released"] += 1
            
            if conn.is_exhausted:
                # Bug 3: removes connection but doesn't decrement total_count
                self.pools[conn.host].remove(conn)
                self.stats["closed"] += 1
            
            # Signal waiters
            self._host_events[conn.host].set()
    
    async def close_idle(self):
        """Close connections idle too long."""
        now = self.time_fn()
        async with self._lock:
            for host, pool in list(self.pools.items()):
                to_remove = []
                for conn in pool:
                    if not conn.is_busy and (now - conn.created_at) > self.max_idle_time:
                        to_remove.append(conn)
                for conn in to_remove:
                    pool.remove(conn)
                    self.total_count -= 1
                    self.stats["closed"] += 1
    
    def get_stats(self):
        return dict(self.stats)
