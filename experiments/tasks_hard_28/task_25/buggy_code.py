"""
Task 25: Event Sourcing with Snapshot Recovery
Category: Hardest — state machine + serialization + system design
"""
import json
import copy
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class Event:
    event_type: str
    data: dict
    version: int
    timestamp: float = 0.0


class EventStore:
    def __init__(self):
        self.events: List[Event] = []
        self.snapshots: Dict[int, dict] = {}  # version -> state snapshot
        self.snapshot_interval = 10
    
    def append(self, event: Event):
        # Bug 1: doesn't validate version ordering — allows out-of-order events
        self.events.append(event)
        
        if len(self.events) % self.snapshot_interval == 0:
            self._take_snapshot()
    
    def _take_snapshot(self):
        state = self.rebuild_state(len(self.events) - 1)
        self.snapshots[len(self.events) - 1] = state
    
    def rebuild_state(self, up_to_version=None):
        """Rebuild state by replaying events."""
        if up_to_version is None:
            up_to_version = len(self.events) - 1
        
        # Find nearest snapshot
        snapshot_version = -1
        state = {}
        
        for sv in sorted(self.snapshots.keys()):
            if sv <= up_to_version:
                snapshot_version = sv
        
        if snapshot_version >= 0:
            # Bug 2: shallow copy of snapshot — mutations affect cached snapshot
            state = self.snapshots[snapshot_version]
            start_idx = snapshot_version + 1
        else:
            start_idx = 0
        
        # Replay events from start_idx to up_to_version
        for i in range(start_idx, up_to_version + 1):
            if i < len(self.events):
                state = self._apply_event(state, self.events[i])
        
        return state
    
    def _apply_event(self, state, event):
        """Apply an event to state. Returns new state."""
        if event.event_type == "set":
            state[event.data["key"]] = event.data["value"]
        elif event.event_type == "delete":
            # Bug 3: doesn't check if key exists before deleting
            state.pop(event.data["key"])
        elif event.event_type == "increment":
            key = event.data["key"]
            amount = event.data.get("amount", 1)
            state[key] = state.get(key, 0) + amount
        elif event.event_type == "merge":
            # Merge dict into state
            state.update(event.data.get("values", {}))
        
        return state
    
    def get_events_since(self, version):
        """Get events after a version."""
        return [e for e in self.events if e.version > version]
    
    def compact(self, keep_after_version):
        """Remove old events, keeping snapshot + events after version."""
        state = self.rebuild_state(keep_after_version)
        self.snapshots = {keep_after_version: state}
        self.events = [e for e in self.events if e.version > keep_after_version]


class Projection:
    """Materialize a view from events."""
    
    def __init__(self, store: EventStore):
        self.store = store
        self.last_version = -1
        self.state = {}
    
    def refresh(self):
        """Update projection from new events."""
        new_events = self.store.get_events_since(self.last_version)
        for event in new_events:
            self.state = self.store._apply_event(self.state, event)
            self.last_version = event.version
    
    def query(self, key):
        self.refresh()
        return self.state.get(key)
