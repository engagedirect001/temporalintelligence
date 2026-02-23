"""
Task 28: Transactional Key-Value Store with MVCC
Category: Hardest — system design + concurrency + data structure + state machine
"""
import threading
import time
from typing import Optional, Dict, Any, List
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Version:
    value: Any
    timestamp: int
    deleted: bool = False
    txn_id: Optional[int] = None


class Transaction:
    def __init__(self, txn_id: int, start_ts: int):
        self.txn_id = txn_id
        self.start_ts = start_ts
        self.read_set: Dict[str, int] = {}   # key -> version timestamp read
        self.write_set: Dict[str, Any] = {}   # key -> value to write
        self.committed = False
        self.aborted = False


class MVCCStore:
    """Multi-Version Concurrency Control key-value store."""
    
    def __init__(self, time_fn=None):
        self.versions: Dict[str, List[Version]] = defaultdict(list)
        self.lock = threading.Lock()
        self.txn_counter = 0
        self.ts_counter = 0
        self.active_txns: Dict[int, Transaction] = {}
        self.committed_txns = set()
        self.time_fn = time_fn or (lambda: None)
    
    def _next_ts(self):
        self.ts_counter += 1
        return self.ts_counter
    
    def begin(self) -> int:
        with self.lock:
            self.txn_counter += 1
            txn_id = self.txn_counter
            start_ts = self._next_ts()
            self.active_txns[txn_id] = Transaction(txn_id, start_ts)
            return txn_id
    
    def read(self, txn_id: int, key: str) -> Optional[Any]:
        with self.lock:
            txn = self.active_txns.get(txn_id)
            if not txn:
                raise RuntimeError("Transaction not active")
            
            # Check write set first (read-your-own-writes)
            if key in txn.write_set:
                return txn.write_set[key]
            
            # Find latest committed version visible to this transaction
            versions = self.versions.get(key, [])
            visible_version = None
            
            for v in reversed(versions):
                # Bug 1: visibility check is wrong — should check if version
                # was committed BEFORE our start_ts, not just timestamp < start_ts
                if v.timestamp <= txn.start_ts:
                    if v.txn_id is None or v.txn_id in self.committed_txns:
                        visible_version = v
                        break
                    # Bug: doesn't skip uncommitted versions from other txns
                    # Falls through and returns None even if there's an older visible version
                    break  # Bug: should continue, not break
            
            if visible_version:
                txn.read_set[key] = visible_version.timestamp
                if visible_version.deleted:
                    return None
                return visible_version.value
            
            return None
    
    def write(self, txn_id: int, key: str, value: Any):
        with self.lock:
            txn = self.active_txns.get(txn_id)
            if not txn:
                raise RuntimeError("Transaction not active")
            txn.write_set[key] = value
    
    def delete(self, txn_id: int, key: str):
        """Delete is a write with a tombstone."""
        self.write(txn_id, key, None)
    
    def commit(self, txn_id: int) -> bool:
        with self.lock:
            txn = self.active_txns.get(txn_id)
            if not txn:
                raise RuntimeError("Transaction not active")
            
            commit_ts = self._next_ts()
            
            # Validation phase: check for write-write conflicts
            for key in txn.write_set:
                versions = self.versions.get(key, [])
                for v in versions:
                    # Bug 2: conflict check window is wrong
                    # Should check for writes with timestamp > start_ts AND < commit_ts
                    if v.timestamp > txn.start_ts and v.txn_id != txn_id:
                        # Write-write conflict
                        self._abort(txn_id)
                        return False
            
            # Bug 3: doesn't validate read set — should check that no
            # committed write happened to any read key since start_ts
            # (this is needed for serializable isolation)
            
            # Install writes
            for key, value in txn.write_set.items():
                version = Version(
                    value=value,
                    timestamp=commit_ts,
                    deleted=(value is None),
                    txn_id=txn_id
                )
                self.versions[key].append(version)
            
            txn.committed = True
            self.committed_txns.add(txn_id)
            del self.active_txns[txn_id]
            return True
    
    def _abort(self, txn_id):
        txn = self.active_txns.get(txn_id)
        if txn:
            txn.aborted = True
            del self.active_txns[txn_id]
    
    def abort(self, txn_id: int):
        with self.lock:
            self._abort(txn_id)
    
    def snapshot_read(self, key: str, as_of_ts: int) -> Optional[Any]:
        """Non-transactional read at a specific timestamp."""
        with self.lock:
            for v in reversed(self.versions.get(key, [])):
                if v.timestamp <= as_of_ts and (v.txn_id in self.committed_txns or v.txn_id is None):
                    if v.deleted:
                        return None
                    return v.value
            return None
